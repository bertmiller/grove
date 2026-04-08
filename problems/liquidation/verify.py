"""Oracle for Task 22: Liquidation Engine (Trading Accounts)."""

import random
import sys
import time

NUM_ACCOUNTS = 200
NUM_INSTRUMENTS = 50
NUM_COMMANDS = 20_000
SEED = 42


def generate_data():
    rng = random.Random(SEED)
    commands = []

    # Create all accounts first
    for _ in range(NUM_ACCOUNTS):
        balance = round(rng.uniform(1000.0, 100000.0), 2)
        commands.append(("account", balance))

    # Set initial prices for all instruments
    instrument_prices = {}
    for i in range(NUM_INSTRUMENTS):
        price = round(rng.uniform(10.0, 1000.0), 2)
        commands.append(("price", i, price))
        instrument_prices[i] = price

    # Generate mixed commands
    remaining = NUM_COMMANDS - NUM_ACCOUNTS - NUM_INSTRUMENTS
    for _ in range(remaining):
        r = rng.random()
        if r < 0.3:
            # Price update
            instr = rng.randint(0, NUM_INSTRUMENTS - 1)
            # Price can move up or down by up to 20%
            old_price = instrument_prices[instr]
            factor = rng.uniform(0.8, 1.2)
            new_price = round(old_price * factor, 2)
            instrument_prices[instr] = new_price
            commands.append(("price", instr, new_price))
        elif r < 0.9:
            # Trade
            acct = rng.randint(0, NUM_ACCOUNTS - 1)
            instr = rng.randint(0, NUM_INSTRUMENTS - 1)
            size = rng.randint(-50, 50)
            if size == 0:
                size = 1
            commands.append(("trade", acct, instr, size))
        else:
            # New account
            balance = round(rng.uniform(1000.0, 100000.0), 2)
            commands.append(("account", balance))

    return commands


def reference_solve(commands):
    accounts = []
    prices = {}
    results = []

    for cmd in commands:
        if cmd[0] == "account":
            balance = cmd[1]
            accounts.append({
                "balance": balance,
                "positions": {},
                "active": True,
            })

        elif cmd[0] == "price":
            instrument_idx = cmd[1]
            price = cmd[2]
            prices[instrument_idx] = price

            # Check all active accounts for liquidation
            to_liquidate = []
            for acct_id, acct in enumerate(accounts):
                if not acct["active"]:
                    continue
                equity = acct["balance"]
                total_notional = 0.0
                for instr, pos in acct["positions"].items():
                    cur_price = prices.get(instr, 0.0)
                    equity += pos["size"] * cur_price - pos["total_paid"]
                    total_notional += abs(pos["size"]) * cur_price
                if equity < total_notional / 100.0:
                    to_liquidate.append((acct_id, equity, total_notional))

            # Sort: largest notional first, then highest account_id first
            to_liquidate.sort(key=lambda x: (-x[2], -x[0]))

            for acct_id, equity, notional in to_liquidate:
                results.append(f"liquidate {acct_id} {equity:.2f} {notional:.2f}")
                accounts[acct_id]["active"] = False
                accounts[acct_id]["balance"] = 0.0
                accounts[acct_id]["positions"] = {}

        elif cmd[0] == "trade":
            account_idx = cmd[1]
            instrument_idx = cmd[2]
            size = cmd[3]
            acct = accounts[account_idx]
            if not acct["active"]:
                continue
            cur_price = prices.get(instrument_idx, 0.0)
            if instrument_idx not in acct["positions"]:
                acct["positions"][instrument_idx] = {"size": 0, "total_paid": 0.0}
            pos = acct["positions"][instrument_idx]
            pos["size"] += size
            pos["total_paid"] += size * cur_price

    return results


def main():
    commands = generate_data()
    expected = reference_solve(commands)

    from solution import solve

    # Warmup
    warmup = [("account", 1000.0), ("price", 0, 100.0), ("trade", 0, 0, 5)]
    solve(warmup)

    start = time.perf_counter()
    result = solve(commands)
    elapsed = time.perf_counter() - start

    if len(result) != len(expected):
        print(
            f"WRONG: got {len(result)} liquidations, expected {len(expected)}",
            file=sys.stderr,
        )
        for i, (r, e) in enumerate(zip(result, expected)):
            if r != e:
                print(f"  First diff at index {i}: got '{r}', expected '{e}'", file=sys.stderr)
                break
        sys.exit(1)

    for i, (r, e) in enumerate(zip(result, expected)):
        if r != e:
            print(
                f"WRONG at liquidation {i}: got '{r}', expected '{e}'",
                file=sys.stderr,
            )
            sys.exit(1)

    print(f"time={elapsed:.6f}")


if __name__ == "__main__":
    main()
