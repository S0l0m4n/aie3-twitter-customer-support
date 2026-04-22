import json


def log_query(entry: dict) -> None:
    print(json.dumps(entry))