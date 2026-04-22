URGENCY_KEYWORDS = {
    "refund", "cancel", "broken", "charged", "stolen", "hacked",
    "urgent", "asap", "immediately", "emergency", "help",
}

NEGATIVE_KEYWORDS = {
    "worst", "terrible", "horrible", "awful", "unacceptable",
    "disgusting", "scam", "fraud", "pathetic",
}


def extract_features(text: str) -> dict:
    """Extract 9 features from a tweet. Must stay identical to the notebook version."""
    # TODO: implement all 9 features using vaderSentiment for sentiment_compound
    return {
        "word_count": 0,
        "char_count": 0,
        "exclamation_count": 0,
        "question_mark_count": 0,
        "caps_ratio": 0.0,
        "urgency_keyword_count": 0,
        "negative_keyword_count": 0,
        "sentiment_compound": 0.0,
        "has_mention": 0,
    }