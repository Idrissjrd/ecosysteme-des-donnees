"""
Golem population model (Group F).
Includes Lotka-Volterra logic and Hybrid Data fetching (Network + Simulation).
"""

import numpy as np
import time
from typing import Dict, Any

# Import the network client
from src.rival import get_vampire_size_from_api


# --- Constants ---
# Golem Parameters (Group F)
GROWTH_RATE = 0.5       # r
K = 1000.0              # Carrying capacity for Golem
ALPHA = 0.2             # Competition coefficient (How much Vampires hurt Golems)

# Simulation Parameters (Used only when API is offline)
K_VAMPIRE_SIM = 1500.0  


def get_vampire_simulation(t: float) -> float:
    """
    Generates a smooth 'Vampire' population curve using math.
    Used ONLY when the Group E API is offline.
    
    Formula: Shifted Cosine to ensure values are always positive [0, K].
    """
    # Returns a value oscillating between 0 and 1500
    return 0.5 * K_VAMPIRE_SIM * (1.0 + np.cos(t * 0.1))


def calculate_next_population(
    current_size: float,
    vampire_size: float,
    growth_rate: float = GROWTH_RATE,
    carrying_capacity: float = K,
    alpha: float = ALPHA
) -> float:
    """
    Calculate next Golem population using Lotka-Volterra competition equation.
    
    dN/dt = r * N * (1 - (N + alpha * N_rival) / K)
    """
    # Avoid division by zero
    if carrying_capacity == 0:
        return 0.0

    # Calculate the "pressure" from both populations
    competition_term = (current_size + alpha * vampire_size) / carrying_capacity
    
    # Calculate next step (Discrete Euler integration)
    # N(t+1) = N(t) + r * N(t) * (1 - competition)
    # Simplified: N * (1 + r * (1 - competition))
    
    next_size = current_size * (1.0 + growth_rate * (1.0 - competition_term))
    
    # Population cannot be negative
    return max(0.0, next_size)


def simulation_step(
    current_size: float,
    growth_rate: float = GROWTH_RATE,
    carrying_capacity: float = K,
    alpha: float = ALPHA
) -> Dict[str, Any]:
    """
    Execute one full simulation step.
    
    1. Fetch Vampire size (Try Network first, then Simulation).
    2. Calculate new Golem size.
    3. Return all data + Connection Status.
    """
    t = time.time()

    # 1. Prepare the Backup Simulation (in case network fails)
    simulated_vampire = get_vampire_simulation(t)
    
    # 2. Fetch Data (Smart Hybrid Mode)
    # Returns: (population_value, is_connected_boolean)
    vampire_pop, is_online = get_vampire_size_from_api(fallback_value=simulated_vampire)

    # 3. Calculate new Golem population
    next_size = calculate_next_population(
        current_size,
        vampire_pop,
        growth_rate,
        carrying_capacity,
        alpha
    )

    # 4. Return Data Package (Matches API expectations)
    return {
        "temps": float(t),
        "taille": float(next_size),
        "vampire": float(vampire_pop),
        
        # New Status Flag for Dashboard Indicator
        "status_vampire": is_online, 
        
        # Metadata
        "taux_de_croissance": float(growth_rate),
        "taux_de_competition": float(alpha),
        "capacite_biotique": float(carrying_capacity),
    }