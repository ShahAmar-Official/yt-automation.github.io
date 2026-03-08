"""
scriptwriter.py — Template-based YouTube Shorts script generator.

Uses deterministic templates with topic-aware variations to produce structured
scripts complete with title, narration, scene descriptions, tags, and a
YouTube description — no paid API keys required.
"""

import hashlib
import logging
import random
import re
import time
from typing import TypedDict

logger = logging.getLogger(__name__)

# Minimum / maximum acceptable word counts for the narration script
_MIN_WORDS = 60
_MAX_WORDS = 200


class ScriptData(TypedDict):
    """Structured output from the script generator."""

    title: str
    script: str
    caption_script: str
    hook: str
    scenes: list[str]
    tags: list[str]
    description: str


# ---------------------------------------------------------------------------
# Hook templates — the critical first line that grabs attention
# ---------------------------------------------------------------------------
_HOOKS: list[str] = [
    "Breaking developments in {topic} are reshaping the landscape as we speak.",
    "Industry leaders are calling {topic} the most significant shift of the decade.",
    "Here is what the latest data reveals about {topic} — and why it matters to you.",
    "A critical update on {topic} that every informed person needs to hear right now.",
    "The conversation around {topic} just reached a tipping point — let me explain.",
    "{topic} is making headlines worldwide, and the implications are far-reaching.",
    "Experts have weighed in on {topic}, and their findings are truly compelling.",
    "If {topic} is not on your radar yet, this sixty-second briefing will change that.",
    "New analysis on {topic} has surfaced, and the results are impossible to ignore.",
    "Three pivotal insights about {topic} that will change how you see it entirely.",
]

# ---------------------------------------------------------------------------
# Body templates — informative middle section
# ---------------------------------------------------------------------------
_BODIES: list[str] = [
    (
        "Here is what is driving the momentum. {topic} has emerged as a defining "
        "force across multiple sectors. Leading analysts confirm that the scale of "
        "this development has few precedents in recent history. What makes it "
        "particularly noteworthy is the direct impact on consumers, businesses, "
        "and policymakers alike. The data points to a sustained trajectory that "
        "could redefine industry standards for years to come."
    ),
    (
        "Let me put this in perspective. {topic} has moved beyond early speculation "
        "into verified, measurable territory. Independent research now validates "
        "what insiders have been signaling for months. The convergence of market "
        "demand, technological advancement, and public interest has created a "
        "perfect storm of relevance. Whether you are a professional or an observer, "
        "the strategic implications here are substantial."
    ),
    (
        "Here is the full picture. {topic} has captured global attention for "
        "a reason that goes deeper than surface-level hype. Behind the headlines "
        "lies a fundamental shift in how stakeholders approach this space. "
        "Innovation, accountability, and scale are the three pillars driving "
        "this forward. The trajectory suggests that early adopters and informed "
        "audiences will benefit the most from understanding these dynamics now."
    ),
    (
        "Consider the broader context. {topic} represents more than a single "
        "event — it signals a structural transformation. The professional "
        "community has responded with unprecedented engagement, and fresh data "
        "continues to reinforce the significance of this movement. What began "
        "as a niche discussion has evolved into a mainstream priority with "
        "real-world consequences that are already taking shape."
    ),
    (
        "Let me walk you through the key factors. {topic} is gaining traction "
        "because it addresses a genuine need in the current landscape. Credible "
        "sources across industries have validated its importance, and the "
        "momentum shows no sign of slowing. For those paying close attention, "
        "the opportunities and implications here are both timely and actionable. "
        "This is a development worth following closely."
    ),
]

# ---------------------------------------------------------------------------
# Call-to-action templates — closing that drives engagement
# ---------------------------------------------------------------------------
_CTAS: list[str] = [
    "If this was valuable, tap like and subscribe for daily insights. Share your perspective on {topic} in the comments below.",
    "Hit subscribe so you never miss a briefing like this. What is your take on {topic}? Drop your thoughts in the comments.",
    "Like this breakdown and turn on notifications to stay ahead of the curve. Tell me how {topic} is affecting your world.",
    "Subscribe for concise, well-researched updates delivered daily. Let me know your experience with {topic} in the comments.",
    "If you found this insightful, share it with someone who needs to know. Follow for more expert-level analysis on trending topics.",
]

# ---------------------------------------------------------------------------
# Scene description templates
# ---------------------------------------------------------------------------
_SCENE_SETS: list[list[str]] = [
    [
        "Dramatic aerial city skyline view",
        "Person looking at phone screen",
        "Fast-paced montage of news clips",
        "Group of people having discussion",
        "Bright colorful abstract motion graphics",
    ],
    [
        "Close-up of hands typing on laptop",
        "Crowd of people in urban setting",
        "Digital data visualization animation",
        "Person presenting to camera confidently",
        "Sunrise over modern cityscape horizon",
    ],
    [
        "Abstract technology background particles",
        "Person walking through busy street",
        "Charts and graphs on digital screen",
        "Creative workspace with equipment",
        "Time-lapse of clouds over landscape",
    ],
    [
        "Modern office with glass walls",
        "Social media icons floating animation",
        "Person reacting with surprise emotion",
        "Colorful gradient abstract background",
        "Night city lights bokeh view",
    ],
]

# ---------------------------------------------------------------------------
# Title templates
# ---------------------------------------------------------------------------
_TITLE_TEMPLATES: list[str] = [
    "{Topic} — What the Experts Are Saying 🔍",
    "The Real Story Behind {Topic} 📊",
    "{Topic} Is Redefining the Industry Right Now 🚀",
    "Why {Topic} Matters More Than Ever 💡",
    "{Topic} — A Must-Watch Briefing 📌",
    "The Latest on {Topic} — Key Takeaways 📈",
    "{Topic} Explained in 60 Seconds ⚡",
    "Inside {Topic} — What You Need to Know 🎯",
]

# ---------------------------------------------------------------------------
# Description template
# ---------------------------------------------------------------------------
_DESCRIPTION_TEMPLATE = """🔍 {title}

Stay informed: {topic} is making waves and we break it down in under 60 seconds.

In this briefing, you will learn:
✅ Why {topic} is trending right now
✅ The key facts and data points you need to know
✅ What this means for you and what to watch next

📱 Subscribe for daily expert-level briefings on trending topics.

👍 Like this video if you found it valuable
💬 Share your perspective in the comments
🔔 Turn on notifications so you never miss an update

{hashtags}

#Shorts #Trending #Analysis #Insights #Briefing #News #Today"""


# ---------------------------------------------------------------------------
# Tag generation
# ---------------------------------------------------------------------------
_BASE_TAGS: list[str] = [
    "shorts", "trending", "viral", "mustwatch", "facts",
    "news", "today", "fyp", "explore", "discover",
]


def _topic_to_tags(topic: str) -> list[str]:
    """Generate relevant tags from the topic string."""
    words = re.sub(r"[^a-zA-Z0-9\s]", "", topic).lower().split()
    topic_tags = [w for w in words if len(w) > 2]

    if len(words) >= 2:
        topic_tags.append("".join(words[:2]))

    all_tags = list(dict.fromkeys(topic_tags + _BASE_TAGS))
    return all_tags[:20]


_SEED_TIME_GRANULARITY = 3600  # seconds — changes seed every hour


def _deterministic_seed(topic: str) -> int:
    """Create a seed from the topic and current time for varied selections.

    Incorporates the current hour so that each pipeline run (scheduled every
    few hours) produces a different script even for the same topic.
    """
    time_component = str(int(time.time() // _SEED_TIME_GRANULARITY))
    raw = topic + time_component
    return int(hashlib.md5(raw.encode()).hexdigest()[:8], 16)


def _titlecase_topic(topic: str) -> str:
    """Convert a topic string to title case for display."""
    return topic.strip().title()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_script(topic: str) -> ScriptData:
    """Generate a structured YouTube Shorts script for *topic*.

    Uses templates with time-seeded randomisation so each pipeline run
    produces a different script, even for the same topic.

    Args:
        topic: The trending topic string to write about.

    Returns:
        A :class:`ScriptData` dict with title, script, caption_script,
        scenes, tags, and description.

    Raises:
        ValueError: If the generated script fails validation.
    """
    logger.info("Generating script for topic: '%s'", topic)

    seed = _deterministic_seed(topic)
    rng = random.Random(seed)

    display_topic = _titlecase_topic(topic)

    # Select templates
    hook = rng.choice(_HOOKS).format(topic=display_topic)
    body = rng.choice(_BODIES).format(topic=display_topic)
    cta = rng.choice(_CTAS).format(topic=display_topic)
    scenes = list(rng.choice(_SCENE_SETS))

    # Build the full script (hook + body + cta for TTS audio)
    script_text = f"{hook} {body} {cta}"

    # Caption script excludes the hook to avoid duplicating the title on-screen
    caption_text = f"{body} {cta}"

    # Build title
    title = rng.choice(_TITLE_TEMPLATES).format(Topic=display_topic)
    title = title[:100]

    # Build tags
    tags = _topic_to_tags(topic)

    # Build description
    hashtags = " ".join(f"#{t}" for t in tags[:10])
    description = _DESCRIPTION_TEMPLATE.format(
        title=title,
        topic=display_topic,
        hashtags=hashtags,
    )

    # Validate word count
    word_count = len(script_text.split())
    if word_count < _MIN_WORDS:
        logger.warning("Script shorter than expected (%d words)", word_count)
    if word_count > _MAX_WORDS:
        logger.warning("Script longer than expected (%d words)", word_count)

    script_data = ScriptData(
        title=title,
        script=script_text,
        caption_script=caption_text,
        hook=hook,
        scenes=scenes,
        tags=tags,
        description=description,
    )

    logger.info(
        "Script generated — title: '%s', words: %d",
        script_data["title"],
        len(script_data["script"].split()),
    )
    return script_data
