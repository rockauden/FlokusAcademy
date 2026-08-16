"""Safety checks applied to a child's message before it reaches the model.

Design notes, because the reasoning matters more than the code here:

* This runs BEFORE the model call, and a match stops that call entirely. An
  LLM must not be the thing that responds to a child disclosing harm — it will
  try to be helpful, and "helpful" in that moment means counselling, which is
  exactly what a general-purpose model should not do with a nine-year-old. The
  reply is a fixed string instead: acknowledge, point at a real adult, point at
  a real service, and stop.

* Detection is phrase-based, not word-based. "kill" or "die" alone would fire
  on "this homework is killing me", which children say constantly; a false
  alarm every afternoon trains a parent to ignore the alerts, which is worse
  than not having them. The phrases below are ones that are hard to say by
  accident.

* It follows that this net has holes. A child who says something oblique will
  pass straight through, and no phrase list fixes that. The real backstop is
  that the parent can read the whole transcript; this layer exists to make sure
  the clearest cases are never missed and are surfaced immediately rather than
  whenever someone next reads the logs.

* Nothing here is sent upstream. The check is local, so a disclosure that trips
  it never reaches Google at all.
"""
import re
from dataclasses import dataclass
from typing import Optional

# The categories a parent would want distinguished at a glance.
SELF_HARM = "self_harm"
ABUSE = "abuse"
DISTRESS = "distress"

# Ordered by severity: the first match wins, so self-harm outranks distress
# when a message could read as either.
_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    (
        SELF_HARM,
        (
            r"\bkill(?:ing)?\s+(?:my\s?self|meself)\b",
            r"\bend\s+(?:my|it)\s+(?:life|all)\b",
            r"\b(?:want|wanna|going)\s+to\s+die\b",
            r"\bwish\s+i\s+(?:was|were)\s+dead\b",
            r"\bhurt(?:ing)?\s+my\s?self\b",
            r"\bcut(?:ting)?\s+my\s?self\b",
            r"\bsuicid(?:e|al)\b",
            r"\bdon'?t\s+want\s+to\s+(?:be\s+alive|live)\b",
        ),
    ),
    (
        ABUSE,
        (
            r"\b(?:hits|hit|beats|beat|hurts|hurt)\s+me\b",
            r"\btouch(?:ed|ing|es)\s+me\b",
            r"\bscared\s+(?:to\s+go\s+home|of\s+(?:him|her|them|my\s+\w+))\b",
            r"\bafraid\s+to\s+go\s+home\b",
            r"\bmade\s+me\s+keep\s+a\s+secret\b",
            r"\bnot\s+allowed\s+to\s+tell\b",
        ),
    ),
    (
        DISTRESS,
        (
            r"\bhate\s+my\s?self\b",
            r"\bnobody\s+(?:loves|likes|cares\s+about)\s+me\b",
            r"\bwant\s+to\s+run\s+away\b",
            r"\beveryone\s+would\s+be\s+better\s+off\s+without\s+me\b",
            r"\bi'?m\s+worthless\b",
        ),
    ),
]

_COMPILED = [
    (category, [re.compile(pattern, re.IGNORECASE) for pattern in patterns])
    for category, patterns in _PATTERNS
]

# Shown to the child verbatim. Deliberately short, warm, and free of questions:
# asking a follow-up would be the model counselling by another route, and a
# child in distress should be talking to a person, not a screen. The last line
# is there because telling him what happens next is both honest and, for a
# nine-year-old in a parent-run school, reassuring rather than punitive.
ESCALATION_REPLY = (
    "Thank you for telling me that. I'm just a study helper, so this is "
    "something to share with your dad or another grown-up you trust - please "
    "go and find them now.\n\n"
    "If you ever want to talk to someone straight away, you can call or text "
    "988 to reach people who help with hard feelings, any time of day.\n\n"
    "I've let your dad know you told me this, so he can check in with you."
)

# How much of the child's message is copied onto the alert. Enough for a parent
# to know what they are walking into; the full text stays in the transcript.
EXCERPT_LIMIT = 300


@dataclass(frozen=True)
class SafetyFinding:
    category: str
    excerpt: str


def check_message(message: str) -> Optional[SafetyFinding]:
    """Return a finding if the message needs a parent's attention, else None."""
    if not message:
        return None

    for category, patterns in _COMPILED:
        for pattern in patterns:
            if pattern.search(message):
                excerpt = message.strip()
                if len(excerpt) > EXCERPT_LIMIT:
                    excerpt = excerpt[:EXCERPT_LIMIT].rstrip() + "..."
                return SafetyFinding(category=category, excerpt=excerpt)

    return None
