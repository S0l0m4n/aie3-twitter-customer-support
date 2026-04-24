import re

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

URGENCY_KEYWORDS = {
    "refund", "cancel", "broken", "charged", "stolen", "hacked",
    "urgent", "asap", "immediately", "emergency", "help",
}

NEGATIVE_KEYWORDS = {
    "worst", "terrible", "horrible", "awful", "unacceptable",
    "disgusting", "scam", "fraud", "pathetic",
}

_vader = SentimentIntensityAnalyzer()


def _tokens(text: str) -> list[str]:
    return [re.sub(r"[^a-z0-9]", "", w.lower()) for w in text.split()]


def word_count(text: str) -> int:
    return len(text.split())


def char_count(text: str) -> int:
    return len(text)


def urgency_keyword_count(text: str) -> int:
    return sum(1 for t in _tokens(text) if t in URGENCY_KEYWORDS)


def negative_keyword_count(text: str) -> int:
    return sum(1 for t in _tokens(text) if t in NEGATIVE_KEYWORDS)


def allcaps_count(text: str) -> int:
    return sum(1 for w in text.split() if w.isalpha() and len(w) > 1 and w == w.upper())


def exclamation_count(text: str) -> int:
    return text.count("!")


def question_mark_count(text: str) -> int:
    return text.count("?")


def sentiment_compound(text: str) -> float:
    return _vader.polarity_scores(text)["compound"]


def extract_features(text: str) -> dict:
    """Extract features from a tweet. Must stay identical to the notebook version."""
    return {
        "word_count": word_count(text),
#       "char_count": char_count(text),     <-- not used by the model
        "urgency_keyword_count": urgency_keyword_count(text),
        "negative_keyword_count": negative_keyword_count(text),
        "allcaps_count": allcaps_count(text),
        "exclamation_count": exclamation_count(text),
        "question_mark_count": question_mark_count(text),
        "sentiment_compound": sentiment_compound(text),
    }
