from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTFLOWKIT_SRC = REPO_ROOT / "libs" / "agentflowkit"
if str(AGENTFLOWKIT_SRC) not in sys.path:
    sys.path.insert(0, str(AGENTFLOWKIT_SRC))

from agentflowkit import OpenAICompatibleChatModel  # noqa: E402


def main() -> None:
    client = OpenAICompatibleChatModel.from_env()
    content = client.complete(
        (
            {
                "role": "system",
                "content": "Return strict JSON only.",
            },
            {
                "role": "user",
                "content": (
                    "Return {\"ok\": true, \"provider\": \"grok\"} if this "
                    "OpenAI-compatible chat completion request works."
                ),
            },
        )
    )
    print(json.dumps({"raw_content": content}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
