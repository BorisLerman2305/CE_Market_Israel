"""
Phase 2: AI-powered competitor model matching via Claude API.

Setup: add your Anthropic API key to .streamlit/secrets.toml:
    ANTHROPIC_API_KEY = "sk-ant-..."

Falls back to Phase 1 (rank + numeric) automatically if no key is found.
Results are cached for 24 h to minimise API calls.
"""

import os
import streamlit as st


def _api_key() -> str | None:
    try:
        k = st.secrets.get("ANTHROPIC_API_KEY", "")
        if k:
            return k
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY") or None


@st.cache_data(show_spinner=False, ttl=86_400)
def ai_match(
    category_he: str,
    base_mfr: str,
    base_model: str,
    comp_mfr: str,
    comp_models: tuple[str, ...],   # tuple → hashable for cache key
) -> str | None:
    """
    Ask Claude to pick the most technically comparable model.
    Returns a model name (guaranteed to be in comp_models) or None.
    comp_models must be a tuple (not list) for Streamlit cache hashing.
    """
    key = _api_key()
    if not key:
        return None

    try:
        import anthropic

        prompt = (
            f"Equipment category: {category_he}\n"
            f"Base model: {base_mfr} {base_model}\n"
            f"Competitor manufacturer: {comp_mfr}\n"
            f"Available competitor models: {', '.join(comp_models)}\n\n"
            f"Which competitor model is the closest technical match to "
            f"{base_mfr} {base_model}?\n"
            f"Consider: operating weight, engine power, application, size class.\n"
            f"Reply with ONLY the exact model name from the list. Nothing else."
        )

        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=40,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = msg.content[0].text.strip()

        # Exact match
        if answer in comp_models:
            return answer
        # Case-insensitive / substring fallback
        au = answer.upper()
        for m in comp_models:
            if au == m.upper() or au in m.upper() or m.upper() in au:
                return m
        return None

    except Exception:
        return None
