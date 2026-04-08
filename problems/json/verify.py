import random
import json
import time
import sys

EXCHANGE_RATES = {
    "USD": 1.0,
    "GBP": 1.3,
    "RUB": 0.013,
    "JPY": 0.0067,
    "CHF": 1.1,
}

CURRENCIES = list(EXCHANGE_RATES.keys())

def generate_data(n_records=500_000, seed=42):
    """Generate n JSON records, one per line."""
    rng = random.Random(seed)
    lines = []
    for _ in range(n_records):
        user_id = rng.randint(1, 100_000)
        currency = rng.choice(CURRENCIES)
        n_txns = rng.randint(1, 10)
        transactions = []
        for _ in range(n_txns):
            amount = round(rng.uniform(0.01, 10000.0), 2)
            to_user_id = rng.randint(1, 100_000)
            canceled = rng.random() < 0.2
            transactions.append({
                "amount": amount,
                "to_user_id": to_user_id,
                "canceled": canceled,
            })
        record = {
            "user_id": user_id,
            "currency": currency,
            "transactions": transactions,
        }
        lines.append(json.dumps(record))
    return '\n'.join(lines)

def reference_solve(json_lines):
    """Reference solution: parse each line, sum external non-canceled amounts in USD."""
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

def main():
    json_lines = generate_data()

    # Compute expected answer
    expected = reference_solve(json_lines)

    import solution

    # Timed run
    t0 = time.perf_counter()
    result = solution.solve(json_lines)
    t1 = time.perf_counter()

    # Verify
    if not isinstance(result, (int, float)):
        print(f"ERROR: result is not a number, got {type(result)}", file=sys.stderr)
        sys.exit(1)
    if abs(result - expected) > 0.01:
        print(f"ERROR: expected {expected:.6f}, got {result:.6f}, diff={abs(result-expected):.6f}", file=sys.stderr)
        sys.exit(1)

    elapsed = t1 - t0
    print(f"time={elapsed:.6f}")

if __name__ == "__main__":
    main()
