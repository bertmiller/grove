# Task 10: JSON Transactions

## Problem

Parse JSON records (one per line) and return the total amount of external, non-canceled transactions converted to USD.

## Interface

```python
def solve(json_lines: str) -> float:
    """Calculate total USD amount of external non-canceled transactions.

    Args:
        json_lines: String containing one JSON record per line.

    Returns:
        Total amount in USD (float).
    """
```

## JSON Record Format

Each line is a JSON object with this structure:

```json
{
    "user_id": 12345,
    "currency": "USD",
    "transactions": [
        {"amount": 100.50, "to_user_id": 67890, "canceled": false},
        {"amount": 25.00, "to_user_id": 12345, "canceled": false}
    ]
}
```

## Rules

1. **External transaction**: A transaction where `record.user_id != transaction.to_user_id`
2. **Not canceled**: `transaction.canceled` is `false`
3. **Currency conversion** to USD using fixed exchange rates:
   - USD: 1.0
   - GBP: 1.3
   - RUB: 0.013
   - JPY: 0.0067
   - CHF: 1.1
4. Sum the converted amounts of all qualifying transactions across all records

## Constraints

- 500,000 JSON records (one per line)
- Each record has 1-10 transactions
- Result must match reference to within 0.01 (floating point tolerance)

## Example

```python
lines = '{"user_id": 1, "currency": "USD", "transactions": [{"amount": 100.0, "to_user_id": 2, "canceled": false}, {"amount": 50.0, "to_user_id": 1, "canceled": false}]}\n{"user_id": 2, "currency": "GBP", "transactions": [{"amount": 200.0, "to_user_id": 1, "canceled": false}, {"amount": 75.0, "to_user_id": 2, "canceled": true}]}'
solve(lines)
# Transaction 1: user_id=1, to=2, not canceled, USD 100.0 -> 100.0 (external)
# Transaction 2: user_id=1, to=1, not canceled -> skip (internal)
# Transaction 3: user_id=2, to=1, not canceled, GBP 200.0 -> 260.0 (external)
# Transaction 4: user_id=2, to=2, canceled -> skip
# Total: 100.0 + 260.0 = 360.0
```
