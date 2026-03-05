"""
scriptwriter.py — Template-based YouTube Shorts script generator.

Produces structured scripts using curated templates and dynamic topic
insertion — no paid API required.
"""

import hashlib
import logging
from typing import TypedDict

logger = logging.getLogger(__name__)

# Minimum / maximum acceptable word counts for the narration script
_MIN_WORDS = 60
_MAX_WORDS = 200


class ScriptData(TypedDict):
    """Structured output from the script generator."""

    title: str
    script: str
    scenes: list[str]
    tags: list[str]
    description: str


# ---------------------------------------------------------------------------
# Script templates — each is a dict with placeholders for {topic}
# ---------------------------------------------------------------------------

_TEMPLATES: list[dict[str, str | list[str]]] = [
    {
        "title": "You Won't Believe This About {topic}!",
        "script": (
            "Stop scrolling — this is something you need to know about {topic}. "
            "Most people have no idea how much {topic} is changing the world right now. "
            "Experts are calling this a game changer and here is why. "
            "First, the impact of {topic} is being felt across every industry. "
            "From technology to everyday life, {topic} is reshaping how we think and act. "
            "Second, the latest developments are moving faster than anyone predicted. "
            "What used to take years is now happening in months. "
            "Third, if you are not paying attention to {topic} right now, you are already behind. "
            "The people who understand this early are the ones who will benefit the most. "
            "So here is what you need to do — stay informed, stay curious, and stay ahead. "
            "Follow for more updates on {topic} and drop a comment with your thoughts. "
            "Hit that subscribe button so you never miss out!"
        ),
        "scenes": [
            "Person looking shocked at phone",
            "News headlines on screen",
            "People discussing in meeting",
            "Technology innovation montage",
            "Person giving thumbs up",
        ],
        "tags": [
            "{topic}", "trending", "viral", "facts", "didyouknow",
            "education", "learning", "mindblown", "shorts", "ytshorts",
            "explore", "discover", "news", "update", "mustwatch",
        ],
    },
    {
        "title": "The Truth About {topic} Nobody Tells You",
        "script": (
            "Wait — did you know this about {topic}? "
            "I just found out something wild, and I had to share it with you. "
            "Everyone is talking about {topic} right now, but nobody is mentioning the full story. "
            "Here is what is really going on. "
            "The buzz around {topic} is not just hype — there are real reasons people are paying attention. "
            "Studies and reports are showing massive shifts related to {topic}. "
            "This affects you, whether you realize it or not. "
            "The smartest thing you can do right now is learn about {topic} before everyone else catches on. "
            "Knowledge is power, and this is your chance to get ahead. "
            "If you found this helpful, smash that like button and subscribe for more content like this. "
            "Share this with someone who needs to hear it!"
        ),
        "scenes": [
            "Person whispering a secret",
            "Stack of books and research",
            "World map with highlights",
            "Graph showing upward trend",
            "Person pointing at camera",
        ],
        "tags": [
            "{topic}", "truth", "revealed", "secrets", "knowledge",
            "information", "trending", "viral", "shorts", "ytshorts",
            "mustknow", "education", "facts", "reality", "exposed",
        ],
    },
    {
        "title": "Why Everyone Is Talking About {topic}",
        "script": (
            "Have you noticed everyone is talking about {topic}? "
            "There is a reason this is blowing up, and I am about to break it down for you. "
            "First, {topic} has been making headlines everywhere. "
            "From social media to major news outlets, it is impossible to ignore. "
            "The reason is simple — {topic} has the potential to change everything. "
            "People are excited, curious, and a little bit worried all at the same time. "
            "But here is the thing — change is not always bad. "
            "In fact, the opportunities coming from {topic} could be incredible. "
            "The key is to stay informed and be ready to adapt. "
            "That is exactly why you should follow this channel. "
            "We break down trending topics like {topic} every single day. "
            "Like, subscribe, and turn on notifications so you never miss an update!"
        ),
        "scenes": [
            "Group of people looking at screen",
            "Social media feeds scrolling",
            "Breaking news broadcast",
            "Lightbulb moment illustration",
            "Hand pressing subscribe button",
        ],
        "tags": [
            "{topic}", "everyone", "talking", "trending", "breakingnews",
            "explained", "breakdown", "viral", "shorts", "ytshorts",
            "socialmedia", "updates", "daily", "mustsee", "followme",
        ],
    },
    {
        "title": "{topic} — 5 Things You Need to Know Right Now",
        "script": (
            "Here are five things you absolutely need to know about {topic} right now. "
            "Number one — {topic} is trending for a very good reason. "
            "Something major just happened and it is making waves everywhere. "
            "Number two — the impact is bigger than you think. "
            "This is not just a passing trend, it is a real shift that affects all of us. "
            "Number three — experts are weighing in and the consensus is clear. "
            "{topic} is here to stay and it is only going to grow from here. "
            "Number four — there are both opportunities and challenges ahead. "
            "The people who prepare now will come out on top. "
            "And number five — you heard it here first. "
            "Stay tuned to this channel for the latest updates on {topic} and more. "
            "Like this video if you learned something new and subscribe for daily content!"
        ),
        "scenes": [
            "Hand counting five fingers",
            "Newspaper headlines close-up",
            "Expert speaking at podium",
            "Person thinking with hand on chin",
            "Celebration with confetti",
        ],
        "tags": [
            "{topic}", "top5", "thingstoknow", "facts", "listicle",
            "education", "learning", "trending", "shorts", "ytshorts",
            "viral", "important", "mustsee", "daily", "knowledge",
        ],
    },
    {
        "title": "This Changes Everything — {topic} Explained",
        "script": (
            "This changes everything — let me explain {topic} in under a minute. "
            "You have probably seen {topic} popping up everywhere lately. "
            "But do you actually understand what is happening and why it matters? "
            "Let me break it down simply. "
            "{topic} is making waves because it challenges what we thought we knew. "
            "New information has come to light and people are taking notice. "
            "This is not something you can afford to ignore. "
            "Whether you are a student, a professional, or just curious, {topic} affects you. "
            "The good news is that understanding it is not that hard. "
            "You just need the right information from the right sources. "
            "That is what this channel is all about — making complex topics simple. "
            "Subscribe and hit the bell so you are always in the loop!"
        ),
        "scenes": [
            "Dramatic reveal moment",
            "Person explaining on whiteboard",
            "Infographic animation",
            "Diverse people watching together",
            "Bell notification icon",
        ],
        "tags": [
            "{topic}", "explained", "gamechanging", "simple", "breakdown",
            "education", "learning", "trending", "shorts", "ytshorts",
            "viral", "information", "guide", "howto", "subscribe",
        ],
    },
]


def _pick_template(topic: str) -> dict[str, str | list[str]]:
    """Deterministically pick a template based on the topic string.

    Uses a hash so the same topic always produces the same template,
    ensuring consistency if the pipeline is re-run.
    """
    idx = int(hashlib.sha256(topic.encode()).hexdigest(), 16) % len(_TEMPLATES)
    return _TEMPLATES[idx]


def _fill_template(template: dict[str, str | list[str]], topic: str) -> ScriptData:
    """Fill a template with the given *topic*."""
    raw_title = str(template["title"]).format(topic=topic).strip()
    # Truncate at word boundary if title exceeds 100 characters
    if len(raw_title) > 100:
        raw_title = raw_title[:97].rsplit(" ", 1)[0] + "…"
    title = raw_title
    script = str(template["script"]).format(topic=topic).strip()
    scenes = [str(s) for s in template["scenes"]]  # type: ignore[union-attr]
    raw_tags = [str(t).format(topic=topic).strip().lstrip("#") for t in template["tags"]]  # type: ignore[union-attr]

    # Build a YouTube description
    tag_line = " ".join(f"#{t}" for t in raw_tags[:10])
    description = (
        f"{title}\n\n"
        f"In this Short, we explore {topic} — what it means, why it matters, "
        f"and what you need to know right now.\n\n"
        f"This channel covers the latest trending topics, "
        f"breaking news, and fascinating stories every single day. "
        f"Subscribe to stay ahead of the curve!\n\n"
        f"🔔 Turn on notifications so you never miss an upload.\n"
        f"👍 Like this video if you found it valuable.\n"
        f"💬 Drop a comment and let us know your thoughts.\n\n"
        f"{tag_line}"
    )

    return ScriptData(
        title=title,
        script=script,
        scenes=scenes,
        tags=raw_tags,
        description=description,
    )


def generate_script(topic: str) -> ScriptData:
    """Generate a structured YouTube Shorts script for *topic*.

    Uses curated templates filled with the given topic — completely free,
    no paid API required.

    Args:
        topic: The trending topic string to write about.

    Returns:
        A :class:`ScriptData` dict with title, script, scenes, tags, and
        description.

    Raises:
        ValueError: If the generated script fails validation.
    """
    logger.info("Generating script for topic: '%s'", topic)
    template = _pick_template(topic)
    script_data = _fill_template(template, topic)

    word_count = len(script_data["script"].split())
    if word_count < _MIN_WORDS:
        raise ValueError(f"Script too short ({word_count} words; min={_MIN_WORDS})")

    logger.info(
        "Script generated — title: '%s', words: %d",
        script_data["title"],
        word_count,
    )
    return script_data
