import re
from langchain_core.output_parsers import StrOutputParser
from config import get_llm
from prompts import (
    sql_prompt,
    table_selector_prompt,
    answer_prompt,
    sql_fix_prompt,
    relevance_prompt,
    fallback_prompt,
)

llm = get_llm()

sql_chain           = sql_prompt           | llm | StrOutputParser()
answer_chain        = answer_prompt        | llm | StrOutputParser()
table_selector_chain = table_selector_prompt | llm | StrOutputParser()
sql_fix_chain       = sql_fix_chain        = sql_fix_prompt | llm | StrOutputParser()
relevance_chain     = relevance_prompt     | llm | StrOutputParser()
fallback_chain      = fallback_prompt      | llm | StrOutputParser()


# ── Prompt-injection patterns ──────────────────────────────────────────────────
# These regex patterns catch common attempts to override system instructions
# inside a user-supplied string.
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"forget\s+(everything|all|your)\s+(you\s+know|instructions?|above)",
    r"you\s+are\s+now\s+(?!a\s+database)",   # "you are now DAN / an evil AI / …"
    r"act\s+as\s+(?!a\s+(database|sql|postgres))",
    r"new\s+system\s+prompt",
    r"<\s*system\s*>",                        # literal <system> tag injection
    r"\\n\s*system\s*:",                      # escaped newline + "system:"
]

_INJECTION_RE = re.compile(
    "|".join(_INJECTION_PATTERNS),
    re.IGNORECASE | re.DOTALL,
)


def _looks_like_injection(text: str) -> bool:
    """Return True when *text* matches any known injection pattern."""
    return bool(_INJECTION_RE.search(text))


def safe_invoke(chain, inputs: dict, fallback: str = "__INJECTION__") -> str:
    """
    Invoke *chain* with *inputs* after screening every string value for
    prompt-injection attempts.

    If an injection is detected, *fallback* is returned immediately without
    ever calling the LLM, so no tokens are spent and no system prompt is
    exposed to the attacker.

    Parameters
    ----------
    chain    : Any LangChain Runnable
    inputs   : dict passed to chain.invoke()
    fallback : value to return when injection is detected (default ``"__INJECTION__"``)
    """
    for value in inputs.values():
        if isinstance(value, str) and _looks_like_injection(value):
            return fallback

    return chain.invoke(inputs)