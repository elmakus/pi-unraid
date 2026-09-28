#!/usr/bin/env python3
"""Canonical pi-unraid selection policy for tests that invoke a real LLM."""

from __future__ import annotations

import argparse
import json

TEST_PROVIDER = "pi"
TEST_MODEL = "codex-lb/gpt-6-luna"
TEST_THINKING = "low"
FORBIDDEN_TEST_MODEL = "codex-lb/gpt-6-astra"


class LlmTestPolicyError(ValueError):
    pass


def validate_llm_test_selection(*, model: str, thinking: str) -> None:
    if model == FORBIDDEN_TEST_MODEL:
        raise LlmTestPolicyError("gpt-6-astra is forbidden for LLM-backed test traffic")
    if model != TEST_MODEL or thinking != TEST_THINKING:
        raise LlmTestPolicyError(
            f"LLM-backed tests must use {TEST_MODEL} with thinking={TEST_THINKING}; "
            "no fallback/substitution is allowed"
        )


def paseo_cli_selection() -> list[str]:
    validate_llm_test_selection(model=TEST_MODEL, thinking=TEST_THINKING)
    return ["--provider", TEST_PROVIDER, "--model", TEST_MODEL, "--thinking", TEST_THINKING]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=TEST_MODEL)
    parser.add_argument("--thinking", default=TEST_THINKING)
    args = parser.parse_args()
    validate_llm_test_selection(model=args.model, thinking=args.thinking)
    print(json.dumps({
        "provider": TEST_PROVIDER,
        "model": TEST_MODEL,
        "thinking": TEST_THINKING,
        "fallback_allowed": False,
        "astra_allowed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
