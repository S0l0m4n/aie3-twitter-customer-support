import os
import pandas as pd

INPUT = "data/twcs.csv"
OUTPUT = "data/big_sample.csv"
SAMPLE_SIZE = 30_000
RANDOM_STATE = 42

if os.path.exists(OUTPUT):
    print(f"{OUTPUT} already exists, skipping.")
    exit(0)

df = pd.read_csv(INPUT)
print(f"Loaded {len(df):,} rows")

# Keep inbound (customer) tweets only
inbound = df[df["inbound"] == True].copy()
print(f"Inbound tweets: {len(inbound):,}")

# Generate the sample from inbound tweets
sample = inbound.sample(n=SAMPLE_SIZE, random_state=RANDOM_STATE)
sample.to_csv(OUTPUT, index=False)
print(f"Saved approx. {SAMPLE_SIZE} entries to {OUTPUT}")
