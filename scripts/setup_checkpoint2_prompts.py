from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.cli import configure_utf8_stdio


PROMPT_NAME = "day13-chat"
PROMPT_V1 = "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}"
PROMPT_V2 = (
    "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}\n"
    "Answer concisely and ground the response in Docs."
)


def client():
    load_dotenv(REPO_ROOT / ".env")
    if not os.getenv("LANGFUSE_PUBLIC_KEY") or not os.getenv("LANGFUSE_SECRET_KEY"):
        raise SystemExit("Thiếu LANGFUSE_PUBLIC_KEY hoặc LANGFUSE_SECRET_KEY trong .env")
    from langfuse import get_client

    langfuse = get_client()
    if not langfuse.auth_check():
        raise SystemExit("Langfuse authentication failed")
    return langfuse


def version_labels(langfuse, version: int) -> list[str]:
    return list(langfuse.get_prompt(PROMPT_NAME, version=version).labels)


def setup(langfuse) -> None:
    existing = langfuse.api.prompts.list(name=PROMPT_NAME, limit=50)
    if existing.data:
        raise SystemExit(
            f"Prompt {PROMPT_NAME} đã tồn tại. Dùng lệnh status để kiểm tra trước khi sửa."
        )
    v1 = langfuse.create_prompt(
        name=PROMPT_NAME,
        prompt=PROMPT_V1,
        labels=["baseline", "production"],
        tags=["day13", "checkpoint-2"],
        commit_message="Checkpoint 2 baseline prompt",
    )
    v2 = langfuse.create_prompt(
        name=PROMPT_NAME,
        prompt=PROMPT_V2,
        labels=["candidate"],
        tags=["day13", "checkpoint-2"],
        commit_message="Checkpoint 2 candidate prompt",
    )
    print(f"created_v1={v1.version} labels={','.join(v1.labels)}")
    print(f"created_v2={v2.version} labels={','.join(v2.labels)}")


def set_production(langfuse, target_version: int) -> None:
    for version in (1, 2):
        labels = [
            label
            for label in version_labels(langfuse, version)
            if label not in {"latest", "production"}
        ]
        if version == target_version:
            labels.append("production")
        langfuse.api.prompt_version.update(
            PROMPT_NAME,
            version,
            new_labels=sorted(set(labels)),
        )
    action = "rollback" if target_version == 1 else "promote"
    print(f"action={action} production_version={target_version}")


def status(langfuse) -> None:
    for version in (1, 2):
        prompt = langfuse.get_prompt(PROMPT_NAME, version=version, cache_ttl_seconds=0)
        print(f"version={version} labels={','.join(sorted(prompt.labels))}")


def main() -> None:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Quản lý prompt cho Checkpoint 2")
    parser.add_argument("action", choices=("setup", "status", "promote", "rollback"))
    args = parser.parse_args()
    langfuse = client()
    if args.action == "setup":
        setup(langfuse)
    elif args.action == "status":
        status(langfuse)
    elif args.action == "promote":
        set_production(langfuse, 2)
    else:
        set_production(langfuse, 1)


if __name__ == "__main__":
    main()
