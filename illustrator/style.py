"""Fixed visual style guide shared by every generated illustration.

Calibrated against the reference slides supplied by the user: professional
flat icon infographics (government building, scales of justice, businessperson,
warning triangle, coins, checklists) in a blue corporate e-learning palette --
NOT a cute cartoon mascot. Keeping this in one place is what makes the whole
set look like it belongs to a single deck: same icon family, same palette,
same line/shading language.
"""

MASCOT_NAME_KO = "브리피"
MASCOT_NAME_EN = "Briffy"

# Optional secondary character, off by default -- the reference slides use
# topic-appropriate icons (bank, scales, businessperson...) rather than one
# recurring cartoon character, so consistency comes from the icon style and
# palette below, not from a fixed mascot.
MASCOT_DESCRIPTION = (
    "a small, friendly, round cloud-shaped mascot character named Briffy, "
    "simple dot eyes, flat vector illustration, gradient body from sky blue to "
    "deep blue, soft rounded silhouette, drawn in the same flat icon line/shading "
    "style as the rest of the illustration"
)

PALETTE = {
    "navy": "#173A8A",
    "primary_blue": "#1E6FD9",
    "sky_blue": "#5FB6E8",
    "pale_blue": "#EAF4FC",
    "white": "#FFFFFF",
}

ICON_SUBJECT_HINT = (
    "government/bank building, law book with scales of justice, businessperson at a laptop, "
    "warning triangle with a document, stack of coins, calculator, checklist, calendar, "
    "shield with a checkmark, house, contract/document with a stamp"
)

STYLE_KEYWORDS = (
    "professional flat vector icon illustration, in the exact style of premium corporate "
    "e-learning icon packs used in Korean business and tax-law training slides "
    "(Flaticon/Freepik-style flat icons), "
    "semi-detailed icons with clean bold outlines and flat color fills -- not overly "
    "minimalist, not childish or cartoonish, "
    "a single icon or a small cluster of 2-3 related icons illustrating one concrete concept "
    f"(subjects like: {ICON_SUBJECT_HINT}), "
    "color palette strictly limited to navy blue, medium blue, sky blue, white and light gray, "
    "isolated on a plain white background, centered composition with generous even padding, "
    "soft subtle drop shadow, flat two-tone shading only, crisp vector edges, print-quality, "
    "high resolution"
)

TEXT_RULE = (
    "the icon artwork itself must contain absolutely NO text, letters, or numerals of any kind -- "
    "titles, labels and definitions are added separately as real, correctly-spelled text "
    "in the slide layout afterwards, not baked into the image"
)

NEGATIVE_RULE = (
    "avoid clutter, avoid busy or colorful backgrounds, avoid warm colors (no red/orange/yellow "
    "as dominant colors), avoid photorealistic rendering, avoid 3D rendering, "
    "avoid any embedded text/letters/numbers, avoid a cute cartoon mascot unless explicitly requested"
)


def build_icon_prompt(concept: str) -> str:
    """Prompt for a single small icon meant to be composited into a
    hand-built infographic layout (numbered card / table / comparison),
    rather than used as a standalone illustration.
    """
    return (
        f"A single isolated professional flat icon on a plain white background. "
        f"Icon subject: {concept}. "
        f"Style: {STYLE_KEYWORDS}. "
        f"Composition: exactly one icon (or one tightly-grouped cluster of 2 related icons), "
        f"centered, square framing, filling most of the frame, no card, no border, no shadow, "
        f"no surrounding scene. "
        f"Text: {TEXT_RULE}. "
        f"Avoid: {NEGATIVE_RULE}."
    )


def build_prompt(concept: str, include_mascot: bool = False) -> str:
    """Compose the final text-to-image prompt for one slide/concept.

    `concept` is a short, concrete icon subject produced by the summarizer,
    e.g. "a government building next to a document with a checkmark".
    """
    mascot_clause = f"You may include {MASCOT_DESCRIPTION} alongside the icon(s). " if include_mascot else ""
    return (
        f"A single professional icon illustration for a Korean online university lecture slide. "
        f"Icon subject: {concept}. "
        f"{mascot_clause}"
        f"Style: {STYLE_KEYWORDS}. "
        f"Text: {TEXT_RULE}. "
        f"Avoid: {NEGATIVE_RULE}. "
        f"Aspect ratio: wide, roughly 4:3."
    )
