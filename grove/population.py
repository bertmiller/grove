"""Population and Individual management for evolutionary search."""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class Individual:
    id: int
    solution_code: str
    fitness: float | None = None
    parent_id: int | None = None
    generation: int = 0
    children_count: int = 0

    @property
    def is_evaluated(self) -> bool:
        return self.fitness is not None

    @property
    def is_valid(self) -> bool:
        return self.fitness is not None


class Population:
    def __init__(self):
        self.individuals: list[Individual] = []
        self._next_id: int = 0
        self._by_id: dict[int, Individual] = {}

    def add(self, solution_code: str, parent_id: int | None = None, generation: int = 0) -> Individual:
        ind = Individual(
            id=self._next_id,
            solution_code=solution_code,
            parent_id=parent_id,
            generation=generation,
        )
        self._next_id += 1
        self.individuals.append(ind)
        self._by_id[ind.id] = ind

        if parent_id is not None and parent_id in self._by_id:
            self._by_id[parent_id].children_count += 1

        return ind

    def get(self, ind_id: int) -> Individual | None:
        return self._by_id.get(ind_id)

    @property
    def valid_individuals(self) -> list[Individual]:
        return [i for i in self.individuals if i.is_valid]

    @property
    def best(self) -> Individual | None:
        valid = self.valid_individuals
        if not valid:
            return None
        return min(valid, key=lambda i: i.fitness)

    def select_parents(self, n: int, tournament_size: int = 3) -> list[Individual]:
        """Select n parents using tournament selection with diversity pressure."""
        valid = self.valid_individuals
        if not valid:
            return []
        if len(valid) <= n:
            return list(valid)

        parents = []
        for _ in range(n):
            candidates = random.sample(valid, min(tournament_size, len(valid)))
            # Score = fitness rank * diversity bonus
            # Lower fitness is better, fewer children is better
            winner = min(candidates, key=lambda i: i.fitness * (1 + i.children_count))
            parents.append(winner)
        return parents

    def survive(self, keep: int) -> list[Individual]:
        """Keep the top `keep` individuals, balancing fitness and diversity.

        Returns the removed individuals.
        """
        valid = self.valid_individuals
        invalid = [i for i in self.individuals if not i.is_valid]

        # Score individuals: fitness with diversity bonus
        # Unique parents in the surviving set is good
        scored = sorted(valid, key=lambda i: i.fitness * (1 + 0.2 * i.children_count))

        survivors = scored[:keep]
        removed = scored[keep:] + invalid

        self.individuals = survivors
        self._by_id = {i.id: i for i in survivors}
        return removed
