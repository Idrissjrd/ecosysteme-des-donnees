"""
Lotka-Volterra population model.

Discrete-time model:
N_i(t+1) = N_i(t) * (1 + r_i * (1 - (N_i(t) + Σ α_ij * N_j(t)) / K_i))
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Species:
    """Species parameters and state."""

    name: str
    size: float  # N_i(t)
    growth_rate: float  # r_i
    carrying_capacity: float  # K_i
    competition: Dict[str, float] = field(default_factory=dict)  # α_ij


class PopulationModel:
    """Lotka-Volterra multi-species model."""

    def __init__(self) -> None:
        self.species: Dict[str, Species] = {}
        self.time_step: int = 0
        self.history: List[Dict] = []

    def add_species(self, sp: Species) -> None:
        """Register a species."""
        self.species[sp.name] = sp

    def set_competition(self, i: str, j: str, alpha: float) -> None:
        """Set competition coefficient α_ij."""
        if i in self.species:
            self.species[i].competition[j] = alpha

    def step(self) -> Dict[str, float]:
        """
        Advance simulation by one time step.

        Returns:
            Dict of species name -> new population size
        """
        new_sizes: Dict[str, float] = {}

        for name, sp in self.species.items():
            # Calculate competition term from other species
            interaction = sum(
                sp.competition.get(other, 0.0) * other_sp.size
                for other, other_sp in self.species.items()
                if other != name
            )

            # Lotka-Volterra formula
            numerator = sp.size + interaction
            factor = 1.0 + sp.growth_rate * (
                1.0 - numerator / sp.carrying_capacity
            )
            new_sizes[name] = max(0.0, sp.size * factor)

        # Update all species
        for name, size in new_sizes.items():
            self.species[name].size = size

        # Record history
        self.time_step += 1
        self.history.append(
            {
                "time": self.time_step,
                "populations": dict(new_sizes),
            }
        )

        return new_sizes

    def get_state(self) -> Dict:
        """Get current simulation state."""
        return {
            "time_step": self.time_step,
            "populations": {
                name: sp.size for name, sp in self.species.items()
            },
        }

    def get_history(self) -> List[Dict]:
        """Get full simulation history."""
        return self.history

    def reset(self) -> None:
        """Reset simulation to initial state."""
        self.time_step = 0
        self.history.clear()


def create_golem_model() -> PopulationModel:
    """
    Create default model for Golem (Group F).

    Golem population depends on Human population.
    """
    model = PopulationModel()

    # Create Golem species (Group F)
    golem = Species(
        name="Golem",
        size=100.0,
        growth_rate=0.5,
        carrying_capacity=1000.0,
    )

    # Create Human species (Group G)
    human = Species(
        name="Human",
        size=150.0,
        growth_rate=0.4,
        carrying_capacity=1500.0,
    )

    model.add_species(golem)
    model.add_species(human)

    # Set competition coefficients
    model.set_competition("Golem", "Human", alpha=0.3)
    model.set_competition("Human", "Golem", alpha=0.2)

    return model
