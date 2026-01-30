"""
Golem population model (Group F).
Synced for Green Light Dashboard.
"""

import numpy as np
import time
from typing import Dict, Any

# Import the network client
from src.rival import get_vampire_size_from_api


# --- Constants ---
GROWTH_RATE = 0.5       # r
K = 1000.0              # Carrying capacity
ALPHA = 0.2             # Competition


def calculate_next_population(
    current_size: float,
    vampire_size: float,
    growth_rate: float = GROWTH_RATE,
    carrying_capacity: float = K,
    alpha: float = ALPHA
) -> float:
    """
    Standard Lotka-Volterra logic.
    """
    if carrying_capacity == 0:
        return 0.0

    competition_term = (current_size + alpha * vampire_size) / carrying_capacity
    next_size = current_size * (1.0 + growth_rate * (1.0 - competition_term))
    
    return max(0.0, next_size)


def simulation_step(
    current_size: float,
    growth_rate: float = GROWTH_RATE,
    carrying_capacity: float = K,
    alpha: float = ALPHA
) -> Dict[str, Any]:
    """
    Execute one full simulation step.
    """
    t = time.time()

    # FIX 1: Do not pass arguments to rival.py (it handles fallbacks internally)
    # Returns: (population_value, is_connected_boolean)
    vampire_pop, is_online = get_vampire_size_from_api()

    # Calculate new Golem population
    next_size = calculate_next_population(
        current_size,
        vampire_pop,
        growth_rate,
        carrying_capacity,
        alpha
    )

    # FIX 2: Use key 'connected' to match api.py
    return {
        "temps": float(t),
        "taille": float(next_size),
        "vampire": float(vampire_pop),
        
        # KEY FIX: This must be 'connected' so api.py can read it!
        "connected": is_online,
        
        # Metadata
        "taux_de_croissance": float(growth_rate),
        "taux_de_competition": float(alpha),
        "capacite_biotique": float(carrying_capacity),
    }