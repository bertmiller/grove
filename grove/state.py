"""Run state tracking and JSON emission for the dashboard."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GenerationSnapshot:
    generation: int
    best_fitness: float | None
    mean_fitness: float | None
    valid_count: int
    total_count: int
    individuals: list[dict]


@dataclass
class RunState:
    problem: str
    run_id: str
    run_dir: Path
    population_size: int
    total_generations: int

    current_generation: int = 0
    start_time: float = field(default_factory=time.time)
    sessions_count: int = 0
    tokens_used: int = 0
    generations: list[GenerationSnapshot] = field(default_factory=list)
    best_individual: dict | None = None
    transcript: list[str] = field(default_factory=list)

    def elapsed_seconds(self) -> float:
        return time.time() - self.start_time

    def log(self, message: str):
        """Add a line to the transcript and print it."""
        print(message)
        self.transcript.append(message)

    def record_generation(self, generation: int, individuals: list):
        """Snapshot a generation's state."""
        valid = [i for i in individuals if i.fitness is not None]
        scores = [i.fitness for i in valid]

        snap = GenerationSnapshot(
            generation=generation,
            best_fitness=min(scores) if scores else None,
            mean_fitness=sum(scores) / len(scores) if scores else None,
            valid_count=len(valid),
            total_count=len(individuals),
            individuals=[
                {
                    "id": i.id,
                    "fitness": i.fitness,
                    "parent_id": i.parent_id,
                    "generation": i.generation,
                }
                for i in individuals
            ],
        )
        self.generations.append(snap)
        self.current_generation = generation

        # Update best
        if valid:
            best = min(valid, key=lambda i: i.fitness)
            self.best_individual = {
                "id": best.id,
                "fitness": best.fitness,
                "generation": best.generation,
                "parent_id": best.parent_id,
            }

    def add_session(self, tokens: int = 0):
        self.sessions_count += 1
        self.tokens_used += tokens

    def to_dict(self) -> dict:
        return {
            "problem": self.problem,
            "run_id": self.run_id,
            "population_size": self.population_size,
            "total_generations": self.total_generations,
            "current_generation": self.current_generation,
            "elapsed_seconds": round(self.elapsed_seconds(), 1),
            "sessions_count": self.sessions_count,
            "tokens_used": self.tokens_used,
            "generations": [
                {
                    "generation": g.generation,
                    "best_fitness": g.best_fitness,
                    "mean_fitness": g.mean_fitness,
                    "valid_count": g.valid_count,
                    "total_count": g.total_count,
                    "individuals": g.individuals,
                }
                for g in self.generations
            ],
            "best_individual": self.best_individual,
            "transcript": self.transcript,
        }

    def emit(self):
        """Write state.json to the run directory."""
        state_path = self.run_dir / "state.json"
        state_path.write_text(json.dumps(self.to_dict(), indent=2))
