"""
Golem population model - Original version.
Uses cos(t) for Vampire population (can be negative).
"""

import numpy as np
import time
from typing import Dict


# Constants
ALPHA = 0.2
GROWTH_RATE = 0.5
K = 1000.0
K_VAMPIRE = 1500.0


def get_vampire_population(t: float = None) -> float:
    """
    Vampire population using cosine function.
    
    Formula: K_vampire * cos(t)
    
    Note: This can return negative values when cos(t) < 0.
    This is mathematically correct for the Lotka-Volterra model
    where negative population represents competitive pressure.
    
    Args:
        t: Time (defaults to current time)
    
    Returns:
        Vampire population (can be negative)
    """
    if t is None:
        t = time.time()
    return K_VAMPIRE * np.cos(t)


def calculate_next_population(
    current_size: float,
    vampire_size: float,
    growth_rate: float = GROWTH_RATE,
    carrying_capacity: float = K,
    alpha: float = ALPHA
) -> float:
    """
    Calculate next Golem population using Lotka-Volterra.
    
    Formula:
    N(t+1) = N(t) * (1 + r * (1 - (N(t) + α * N_vampire(t)) / K))
    
    Args:
        current_size: Current Golem population
        vampire_size: Current Vampire population (can be negative)
        growth_rate: Golem growth rate r
        carrying_capacity: Golem carrying capacity K
        alpha: Competition coefficient α
    
    Returns:
        New Golem population size
    """
    competition = (current_size + alpha * vampire_size) / carrying_capacity
    return current_size * (1.0 + growth_rate * (1.0 - competition))


def simulation_step(
    current_size: float,
    growth_rate: float = GROWTH_RATE,
    carrying_capacity: float = K,
    alpha: float = ALPHA
) -> Dict[str, float]:
    """
    Execute one simulation step.
    
    Args:
        current_size: Current Golem population
        growth_rate: Growth rate
        carrying_capacity: Carrying capacity
        alpha: Competition coefficient
    
    Returns:
        Dict with simulation results
    """
    t = time.time()
    vampire_pop = get_vampire_population(t)
    
    next_size = calculate_next_population(
        current_size,
        vampire_pop,
        growth_rate,
        carrying_capacity,
        alpha
    )
    
    return {
        "temps": float(t),
        "taille": float(next_size),
        "taux_de_croissance": float(growth_rate),
        "taux_de_competition": float(alpha),
        "capacite_biotique": float(carrying_capacity),
        "vampire": float(vampire_pop),
    }

    
