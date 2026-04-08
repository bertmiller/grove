# Liquidation Engine (Trading Accounts)

## Problem

Simulate a simple trading system and detect margin-violation liquidations.

Process a sequence of commands and return a list of liquidation event strings.

## Function Signature

```python
def solve(commands: list[tuple]) -> list[str]:
```

### Parameters
- `commands`: A list of ~20,000 tuples, each one of:
  - `("account", balance)` — Create a new account with the given USD balance (float). Account IDs start at 0 and increment sequentially.
  - `("price", instrument_idx, price)` — Set/update the price of instrument `instrument_idx` (int) to `price` (float). After this command, check all active accounts for margin violations.
  - `("trade", account_idx, instrument_idx, size)` — Account `account_idx` trades `size` units (signed int, positive=buy, negative=sell) of instrument `instrument_idx` at the current price.

### Returns
- A list of strings, one per liquidation event, in the order they occur. Format: `"liquidate {account_id} {equity:.2f} {notional:.2f}"`

## Liquidation Logic

After each `"price"` command, check all active (non-liquidated) accounts:

For each account, compute:
- **equity** = `balance + sum over instruments(size_i * current_price_i - total_paid_i)`
  - `size_i` = net position in instrument i (sum of all trade sizes for that instrument)
  - `current_price_i` = latest price of instrument i
  - `total_paid_i` = cumulative cost basis for instrument i = sum of `(trade_size * price_at_trade_time)` for each trade
- **total_notional** = `sum over instruments(|size_i| * current_price_i)`

If `equity < total_notional / 100`, the account is liquidated:
- Output: `"liquidate {account_id} {equity:.2f} {notional:.2f}"`
- Clear the account (balance=0, all positions cleared). The account is removed from future checks.

**Liquidation ordering** within a single price update: sort by largest `total_notional` first (descending), then by highest `account_id` first (descending) as tiebreaker.

All liquidations for one price update are processed before moving to the next command.

## Example

```python
>>> solve([
...     ("account", 1000.0),        # account 0, balance=1000
...     ("account", 500.0),         # account 1, balance=500
...     ("price", 0, 100.0),        # instrument 0 = $100; no trades yet, no liquidations
...     ("trade", 0, 0, 10),        # account 0 buys 10 of instrument 0 at $100 (cost=1000)
...     ("price", 0, 50.0),         # instrument 0 drops to $50
...     # account 0: equity = 1000 + (10*50 - 1000) = 1000 + (500-1000) = 500
...     #            notional = |10|*50 = 500
...     #            500 < 500/100=5? No.
...     # account 1: no positions, equity=500, notional=0, 500<0? No.
... ])
[]
```

## Notes

- Only check for liquidations after `"price"` commands, not after `"trade"` or `"account"` commands.
- An account with no positions has notional=0. It is only liquidated if equity < 0.
- equity can be negative (e.g., if price moves against a large position).
- There are ~200 accounts, ~50 instruments, and ~20,000 total commands.
- You may use any standard library or numpy for optimization.
