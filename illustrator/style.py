"""Fixed visual style guide shared by every generated illustration.

Keeping this in one place is what makes the whole set look like it belongs
to a single deck: same mascot, same palette, same line/shape language.
"""

MASCOT_NAME_KO = "브리피"
MASCOT_NAME_EN = "Briffy"

MASCOT_DESCRIPTION = (
    "a small, friendly, round cloud-shaped mascot character named Briffy, "
    "simple dot eyes, no mouth or a tiny curved smile, flat vector illustration, "
    "smooth gradient body from sky blue to deep blue, soft rounded silhouette, "
    "no arms/legs details beyond simple flat shapes if needed"
)

PALETTE = {
    "deep_blue": "#1E88E5",
    "sky_blue": "#4FC3F7",
    "pale_blue": "#EAF6FF",
    "white": "#FFFFFF",
    "accent_navy": "#0D47A1",
}

STYLE_KEYWORDS = (
    "flat vector illustration, e-learning courseware icon style, "
    "clean simple shapes, soft rounded corners, consistent 4px line weight, "
    "limited color palette of deep blue, sky blue, pale blue and white, "
    "soft flat shading only, no photorealism, no real human faces, "
    "no gradients other than simple two-tone blends, generous white space, "
    "centered composition, isolated on a very light pale-blue or white background"
)

TEXT_RULE = (
    "absolutely minimize any embedded text; if a label is unavoidable, "
    "use at most one very short word, otherwise leave the illustration free of text or letters"
)

NEGATIVE_RULE = (
    "avoid clutter, avoid busy backgrounds, avoid warm colors (no red/orange/yellow "
    "as dominant colors), avoid photorealistic rendering, avoid small unreadable text"
)


def build_prompt(concept: str, include_mascot: bool = True) -> str:
    """Compose the final text-to-image prompt for one slide/concept.

    `concept` is a short, concrete visual description of what should be drawn
    (produced by the summarizer), e.g. "a cloud storing folders, representing
    data backup".
    """
    mascot_clause = f"Feature {MASCOT_DESCRIPTION} interacting with the scene. " if include_mascot else ""
    return (
        f"An educational courseware illustration for a Korean online university lecture slide. "
        f"{mascot_clause}"
        f"Scene: {concept}. "
        f"Style: {STYLE_KEYWORDS}. "
        f"Text: {TEXT_RULE}. "
        f"Avoid: {NEGATIVE_RULE}. "
        f"Aspect ratio: wide, roughly 4:3."
    )
