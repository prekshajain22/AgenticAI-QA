"""
Diagnostic: send one tiny request to a configured LLM provider.

Not a pytest test. Prints only PASS/FAIL and a short reason, never API keys.

Usage:
    python scripts/check_llm_provider.py            # Gemini (default)
    python scripts/check_llm_provider.py openrouter
"""

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


async def main(provider: str) -> int:
    from autogen_core.models import UserMessage

    from agents.mcp_config import MCPConfig

    factories = {
        "gemini": MCPConfig.gemini_client,
        "openrouter": MCPConfig.openrouter_client,
    }
    if provider not in factories:
        print(f"FAIL: unknown provider '{provider}'. Use one of: {', '.join(factories)}")
        return 2

    try:
        client = factories[provider]()
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 1

    try:
        result = await client.create(
            [UserMessage(content="Reply with the single word: ok", source="user")]
        )
        text = str(result.content).strip()
        print(f"PASS: {provider} responded ({len(text)} chars): {text[:60]!r}")
        return 0
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        status = getattr(exc, "status_code", "n/a")
        print(
            f"FAIL: {provider} request failed "
            f"[{type(exc).__name__}, status={status}]: {str(exc)[:300]}"
        )
        return 1
    finally:
        await client.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "gemini")))
