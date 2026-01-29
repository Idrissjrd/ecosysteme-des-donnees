"""Unit tests for population model."""

import pytest
from src.model import PopulationModel, Species, create_golem_model


class TestSpecies:
    """Test Species dataclass."""

    def test_species_creation(self):
        """Test creating a species."""
        sp = Species(
            name="TestSpecies",
            size=100.0,
            growth_rate=0.5,
            carrying_capacity=1000.0,
        )
        assert sp.name == "TestSpecies"
        assert sp.size == 100.0
        assert sp.growth_rate == 0.5
        assert sp.carrying_capacity == 1000.0


class TestPopulationModel:
    """Test PopulationModel class."""

    def test_model_creation(self):
        """Test creating a model."""
        model = PopulationModel()
        assert model.time_step == 0
        assert len(model.species) == 0
        assert len(model.history) == 0

    def test_add_species(self):
        """Test adding species to model."""
        model = PopulationModel()
        sp = Species("Test", 100.0, 0.5, 1000.0)
        model.add_species(sp)

        assert "Test" in model.species
        assert model.species["Test"].size == 100.0

    def test_set_competition(self):
        """Test setting competition coefficient."""
        model = PopulationModel()
        model.add_species(Species("A", 100.0, 0.5, 1000.0))
        model.add_species(Species("B", 100.0, 0.5, 1000.0))

        model.set_competition("A", "B", 0.3)

        assert model.species["A"].competition.get("B") == 0.3

    def test_single_species_growth(self):
        """Test single species growth (no competition)."""
        model = PopulationModel()
        model.add_species(Species("Solo", 100.0, 0.5, 1000.0))

        # Run one step
        new_sizes = model.step()

        assert model.time_step == 1
        assert "Solo" in new_sizes
        assert new_sizes["Solo"] > 100.0  # Should grow
        assert len(model.history) == 1

    def test_lotka_volterra_dynamics(self):
        """Test Lotka-Volterra with competition."""
        model = create_golem_model()

        # Get initial sizes
        initial_golem = model.species["Golem"].size
        initial_human = model.species["Human"].size

        # Run multiple steps
        for _ in range(10):
            model.step()

        # Verify history is recorded
        assert model.time_step == 10
        assert len(model.history) == 10

        # Verify populations changed (not same as initial)
        final_golem = model.species["Golem"].size
        final_human = model.species["Human"].size

        assert final_golem != initial_golem or final_human != initial_human

    def test_get_state(self):
        """Test getting current state."""
        model = PopulationModel()
        model.add_species(Species("Test", 100.0, 0.5, 1000.0))
        model.step()

        state = model.get_state()

        assert state["time_step"] == 1
        assert "Test" in state["populations"]

    def test_reset(self):
        """Test resetting simulation."""
        model = PopulationModel()
        model.add_species(Species("Test", 100.0, 0.5, 1000.0))

        # Run steps
        for _ in range(5):
            model.step()

        assert model.time_step == 5
        assert len(model.history) == 5

        # Reset
        model.reset()

        assert model.time_step == 0
        assert len(model.history) == 0

    def test_population_stays_positive(self):
        """Test that populations never go negative."""
        model = PopulationModel()
        model.add_species(Species("Test", 0.1, -0.9, 1000.0))  # High death rate

        for _ in range(100):
            sizes = model.step()
            assert sizes["Test"] >= 0.0  # Never negative


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
