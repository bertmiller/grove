import json

EXCHANGE_RATES = {
    "USD": 1.0,
    "GBP": 1.3,
    "RUB": 0.013,
    "JPY": 0.0067,
    "CHF": 1.1,
}

def solve(json_lines: str) -> float:
    """Calculate total USD amount of external non-canceled transactions."""
    total = 0.0
    for line in json_lines.split('\n'):
        if not line.strip():
            continue
        record = json.loads(line)
        user_id = record["user_id"]
        currency = record["currency"]
        rate = EXCHANGE_RATES[currency]
        for txn in record["transactions"]:
            if txn["to_user_id"] != user_id and not txn["canceled"]:
                total += txn["amount"] * rate
    return total
