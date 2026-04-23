"""
Filters twcs.csv down to ~25k first-complaint → first-brand-reply pairs.

Columns: ticket_id, complaint_text, brand_reply, created_at

Should be run from the project root directory.
"""

import pandas as pd

INPUT = "data/twcs.csv"
OUTPUT = "data/first-brand-reply-pairs.csv"
SAMPLE_SIZE = 25_000
RANDOM_STATE = 42

df = pd.read_csv(INPUT)
print(f"Loaded {len(df):,} rows")

# Step 1 — keep inbound (customer) tweets only
inbound = df[df["inbound"] == True].copy()
print(f"Inbound tweets: {len(inbound):,}")

# Step 2 — identify conversation starters
# A tweet is a follow-up if its tweet_id appears as a response_tweet_id
# in another inbound tweet. We need to expand comma-separated response_tweet_ids.
inbound_response_ids = (
    inbound["response_tweet_id"]
    .dropna()
    .astype(str)
    .str.split(",")
    .explode()
    .str.strip()
)
inbound_response_ids = set(inbound_response_ids[pd.to_numeric(inbound_response_ids, errors="coerce").notna()])

starters = inbound[~inbound["tweet_id"].isin(inbound_response_ids)].copy()
print(f"Conversation starters: {len(starters):,}")

# Step 3 — take first response_tweet_id (first brand reply), then join
# response_tweet_id can be comma-separated; first ID = first reply
starters["first_reply_id"] = (
    starters["response_tweet_id"]
    .astype(str)
    .str.split(",")
    .str[0]
    .str.strip()
)
starters["first_reply_id"] = pd.to_numeric(starters["first_reply_id"], errors="coerce")

brand_tweets = df[df["inbound"] == False][["tweet_id", "text"]].rename(
    columns={"tweet_id": "first_reply_id", "text": "brand_reply"}
)

pairs = starters.merge(brand_tweets, on="first_reply_id", how="left")

# Step 4 — drop complaints with no brand reply
pairs = pairs[pairs["brand_reply"].notna()].copy()
print(f"Pairs after dropping orphans: {len(pairs):,}")

# Step 5 — sample 25k
if len(pairs) > SAMPLE_SIZE:
    pairs = pairs.sample(n=SAMPLE_SIZE, random_state=RANDOM_STATE)
    print(f"Sampled down to {len(pairs):,}")

pairs = pairs.rename(columns={"tweet_id": "ticket_id", "text": "complaint_text"})
pairs = pairs[["ticket_id", "complaint_text", "brand_reply", "created_at"]]

pairs.to_csv(OUTPUT, index=False)
print(f"Saved to {OUTPUT}")
