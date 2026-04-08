"""Main evolutionary loop."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from grove.agent import dispatch_agent
from grove.environment import Environment
from grove.population import Population
from grove.scoring import evaluate
from grove.server import start_dashboard_server
from grove.state import RunState


def create_run_dir(problem_name: str) -> Path:
    """Create a timestamped run directory under runs/."""
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    run_id = f"{timestamp}_{problem_name}"
    run_dir = Path.cwd() / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "environments").mkdir(exist_ok=True)
    return run_dir


def evaluate_individual(ind, problem_dir: Path, env_base: Path | None = None):
    """Evaluate an individual by running verify.py in an isolated environment."""
    env = Environment(
        problem_dir,
        solution_code=ind.solution_code,
        base_dir=env_base,
        name=f"eval_{ind.id}",
    )
    try:
        score = evaluate(env.work_dir)
        ind.fitness = score
    finally:
        if env_base is None:
            env.cleanup()


def evolve_individual(
    parent,
    problem_dir: Path,
    generation: int,
    population: Population,
    agent_turns: int,
    state: RunState,
):
    """Create a child from a parent by dispatching an agent to improve the solution."""
    env_base = state.run_dir / "environments"
    child_name = f"ind_{population._next_id}"
    env = Environment(
        problem_dir,
        solution_code=parent.solution_code,
        base_dir=env_base,
        name=child_name,
    )
    try:
        transcript_dir = state.run_dir / "transcripts" / child_name
        result = dispatch_agent(env.work_dir, max_turns=agent_turns, transcript_dir=transcript_dir)
        state.add_session(tokens=result.tokens_used)

        new_code = result.solution_code if result.solution_code else parent.solution_code
        state.log(f"    Solution {'modified' if result.changed else 'unchanged'} by agent")

        child = population.add(
            solution_code=new_code,
            parent_id=parent.id,
            generation=generation,
        )

        # Evaluate in a fresh env for clean state
        eval_env = Environment(
            problem_dir,
            solution_code=new_code,
            base_dir=env_base,
            name=f"eval_{child.id}",
        )
        child.fitness = evaluate(eval_env.work_dir)

        if child.fitness is not None:
            state.log(f"    Child {child.id} score: {child.fitness:.4f}")
        else:
            state.log(f"    Child {child.id} failed verification")

        state.emit()
        return child
    finally:
        pass  # persistent env dirs stay for inspection


def run_evolution(problem_dir: Path, population_size: int, generations: int, agent_turns: int):
    """Run the full evolutionary optimization loop."""
    run_dir = create_run_dir(problem_dir.name)
    env_base = run_dir / "environments"

    state = RunState(
        problem=problem_dir.name,
        run_id=run_dir.name,
        run_dir=run_dir,
        population_size=population_size,
        total_generations=generations,
    )

    # Start dashboard server
    port = start_dashboard_server(state)
    state.log(f"Dashboard: http://localhost:{port}")
    state.log("")

    state.log(f"Problem: {problem_dir.name}")
    state.log(f"Population: {population_size}, Generations: {generations}, Agent turns: {agent_turns}")
    state.log(f"Run dir: {run_dir}")
    state.log("")

    population = Population()
    base_solution = (problem_dir / "solution.py").read_text()

    # --- Generation 0: Baseline ---
    state.log("=== Generation 0: Baseline ===")
    baseline = population.add(solution_code=base_solution, generation=0)
    evaluate_individual(baseline, problem_dir, env_base)

    if baseline.fitness is not None:
        state.log(f"  Baseline score: {baseline.fitness:.4f}")
    else:
        state.log("  Baseline failed verification!")

    state.record_generation(0, population.individuals)
    state.emit()

    # Create initial population
    state.log(f"\n=== Initializing population ({population_size} individuals) ===")
    for i in range(population_size - 1):
        state.log(f"  Creating individual {i + 1}/{population_size - 1}...")
        evolve_individual(baseline, problem_dir, generation=0, population=population, agent_turns=agent_turns, state=state)

    state.record_generation(0, population.individuals)
    state.emit()
    _print_gen_stats(state, 0, population)

    # --- Evolutionary loop ---
    for gen in range(1, generations + 1):
        state.log(f"\n=== Generation {gen}/{generations} ===")

        parents = population.select_parents(population_size)
        if not parents:
            state.log("  No valid parents available, stopping.")
            break

        state.log(f"  Selected {len(parents)} parents: {[p.id for p in parents]}")

        for i, parent in enumerate(parents):
            state.log(f"  Evolving child {i + 1}/{len(parents)} from parent {parent.id} (fitness={parent.fitness:.4f})...")
            evolve_individual(parent, problem_dir, generation=gen, population=population, agent_turns=agent_turns, state=state)

        removed = population.survive(keep=population_size)
        if removed:
            state.log(f"  Removed {len(removed)} individuals")

        state.record_generation(gen, population.individuals)
        state.emit()
        _print_gen_stats(state, gen, population)

    # --- Final Results ---
    state.log("\n=== Final Results ===")
    best = population.best
    if best:
        state.log(f"Best score: {best.fitness:.4f} (individual {best.id}, generation {best.generation})")
        output_path = problem_dir / "solution_best.py"
        output_path.write_text(best.solution_code)
        state.log(f"Best solution saved to: {output_path}")
    else:
        state.log("No valid solutions found.")

    state.emit()


def _print_gen_stats(state: RunState, generation: int, population: Population):
    valid = population.valid_individuals
    if not valid:
        state.log(f"  Gen {generation}: no valid individuals")
        return

    scores = [i.fitness for i in valid]
    best = min(scores)
    mean = sum(scores) / len(scores)
    unique_parents = len(set(i.parent_id for i in valid if i.parent_id is not None))

    state.log(f"  Gen {generation}: best={best:.4f}  mean={mean:.4f}  valid={len(valid)}/{len(population.individuals)}  unique_parents={unique_parents}")

    best_ind = population.best
    if best_ind:
        state.log(f"  Best individual: id={best_ind.id} parent={best_ind.parent_id} gen={best_ind.generation}")
