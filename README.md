![Grove banner](./grove_banner.png)

# Grove

Grove is an evolutionary optimization harness that dispatches Claude agents to iteratively improve code solutions. It is inspired by a grove of trees, as agents in Grove explore many branches in pursuit of the performance frontier.

Give it a problem (defined as a `reference.md` describing the problem, a `solution.py` to optimize and a `verify.py` to score it), and Grove will evolve a population of solutions using Claude as the coding agent. Grove is built to be general and work with many different types of optimization problems, and three examples are provided.

## Prerequisites

- Python 3.10+
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI installed.

Grove invokes the `claude` CLI under the hood, thereby relying on the user's **Claude Code subscription**. Note: Grove strips the user's `ANTHROPIC_API_KEY` in their environment by default to prefer subscription auth; remove that behavior in `agent.py` if you want API billing.

## Setup
* install Claude code
* clone this repo

No dependencies beyond the standard library.

## Usage

```bash
python -m grove run <problem> [--population N] [--generations N] [--turns N]
```

**Arguments:**

| Flag | Default | Description |
|------|---------|-------------|
| `<problem>` | required | Problem directory name under `problems/` |
| `--population` | 5 | Number of individuals in the population |
| `--generations` | 10 | Number of evolutionary generations |
| `--turns` | 25 | Max Claude agent turns per individual |

**Example:**

```bash
python -m grove run liquidation --population 3 --generations 5
```

See below for other problem names.

A dashboard URL is printed on startup (e.g. `http://localhost:8150`). Open it to watch progress, view stats, and read agent transcripts.

## Problems
There are three problems I have added to Grove:
- **json** — Parse newline-delimited JSON records and return the total USD value of external, non-canceled transactions using fixed FX rates in the shortest amount of time possible.
- **kernel** — Lower the cycle count of Anthropic's open source kernel challenge.
- **liquidation** — Simulate accounts, trades, and prices, then after each price update emit liquidation strings for accounts whose equity falls below 1% of notional, in the shortest amount of time possible.

## Adding a problem

Create a directory under `problems/` with:

```
problems/my-problem/
  solution.py   # code to be optimized
  verify.py     # scoring script — prints a numeric score (lower is better)
  reference.md  # optional context for the agent
```

The agent can only edit `solution.py`. It runs `python3 verify.py` to measure its score. The harness also runs `verify.py` to score solutions.

## How it works

1. Baseline `solution.py` is scored via `verify.py`
2. A population of individuals is initialized by dispatching Claude agents to improve the baseline
3. Each generation: parents are selected, agents create children by editing `solution.py`, children are scored
4. Worst individuals are culled; best solution is saved to `problems/<name>/solution_best.py`

## Future functionality
- Require agents to structure their thinking into: analysis, hypothesis, experiment, iteration.
- Require agents to take notes documenting their thinking in writing.
- Share note of parents with children, share sibling notes with each other.
- Change parent selection to balance diversity and fitness (see: ShinkaEvolve)
- Implement some form of novelty testing of ideas
- Experiment with longer running agents implementing many ideas
- Experiment with nudging stagnant agents