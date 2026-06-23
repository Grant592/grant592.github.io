"""Thin wrapper around the Anthropic API so modules don't repeat boilerplate.

Uses Claude (Haiku for cheap drafts, Sonnet for quality). Requires
ANTHROPIC_API_KEY in the environment. Kept deliberately small.
"""
from __future__ import annotations

from .config import env, load_config


def _client():
    try:
        from anthropic import Anthropic
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "The 'anthropic' package is required. Run: pip install -r requirements.txt"
        ) from exc
    key = env("ANTHROPIC_API_KEY")
    if not key:
        raise SystemExit("Set ANTHROPIC_API_KEY in your .env file.")
    return Anthropic(api_key=key)


def complete(prompt: str, *, system: str = "", quality: bool = False,
             max_tokens: int = 1500) -> str:
    """Return the model's text response to a single prompt."""
    cfg = load_config()["llm"]
    model = cfg["quality_model"] if quality else cfg["draft_model"]
    msg = _client().messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system or "You are an expert SEO copywriter for a UK wedding photographer.",
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in msg.content if block.type == "text").strip()


def ask_with_image(prompt: str, image_bytes: bytes, media_type: str = "image/jpeg",
                   max_tokens: int = 300) -> str:
    """Vision call — used for image alt text."""
    import base64

    cfg = load_config()["llm"]
    msg = _client().messages.create(
        model=cfg["vision_model"],
        max_tokens=max_tokens,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {
                    "type": "base64", "media_type": media_type,
                    "data": base64.standard_b64encode(image_bytes).decode(),
                }},
                {"type": "text", "text": prompt},
            ],
        }],
    )
    return "".join(b.text for b in msg.content if b.type == "text").strip()
