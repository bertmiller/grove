import argparse
import sys
from pathlib import Path

from grove.harness import run_evolution


def main():
    parser = argparse.ArgumentParser(description="Grove evolutionary optimization harness")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run evolutionary optimization on a problem")
    run_parser.add_argument("problem", help="Problem name (directory under problems/)")
    run_parser.add_argument("--population", type=int, default=5, help="Population size (default: 5)")
    run_parser.add_argument("--generations", type=int, default=10, help="Number of generations (default: 10)")
    run_parser.add_argument("--turns", type=int, default=25, help="Max agent interaction turns (default: 25)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "run":
        problems_dir = Path.cwd() / "problems"
        problem_dir = problems_dir / args.problem

        if not problem_dir.exists():
            print(f"Error: Problem '{args.problem}' not found in {problems_dir}")
            available = [p.name for p in problems_dir.iterdir() if p.is_dir()] if problems_dir.exists() else []
            if available:
                print(f"Available problems: {', '.join(sorted(available))}")
            sys.exit(1)

        if not (problem_dir / "verify.py").exists():
            print(f"Error: {problem_dir / 'verify.py'} not found")
            sys.exit(1)

        if not (problem_dir / "solution.py").exists():
            print(f"Error: {problem_dir / 'solution.py'} not found")
            sys.exit(1)

        run_evolution(
            problem_dir=problem_dir,
            population_size=args.population,
            generations=args.generations,
            agent_turns=args.turns,
        )
