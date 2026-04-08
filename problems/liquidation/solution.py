def solve(commands: list[tuple]) -> list[str]:
    accounts = []       # list of dicts: {balance, positions: {instr: {size, total_paid}}, active}
    prices = {}         # instrument_idx -> current price
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
