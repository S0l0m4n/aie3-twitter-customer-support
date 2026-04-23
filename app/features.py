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
    """Lowercase word tokens, punctuation stripped from edges."""
    return [re.sub(r"[^a-z0-9]", "", w.lower()) for w in text.split()]


def extract_features(text: str) -> dict:
    """Extract 9 features from a tweet. Must stay identical to the notebook version."""
    words = text.split()
    tokens = _tokens(text)

    # caps_ratio: fraction of words that are ALL-CAPS alphabetic (length > 1)
    caps_words = sum(1 for w in words if w.isalpha() and len(w) > 1 and w == w.upper())
    caps_ratio = caps_words / len(words) if words else 0.0

    return {
        "word_count": len(words),
        "char_count": len(text),
        "exclamation_count": text.count("!"),
        "question_mark_count": text.count("?"),
        "caps_ratio": caps_ratio,
        "urgency_keyword_count": sum(1 for t in tokens if t in URGENCY_KEYWORDS),
        "negative_keyword_count": sum(1 for t in tokens if t in NEGATIVE_KEYWORDS),
        "sentiment_compound": _vader.polarity_scores(text)["compound"],
        "has_mention": int(bool(re.search(r"@\w+", text))),
    }