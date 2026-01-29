"""
REST API for population model with database storage.
Port: 16050 (Golem - Group F)
Authors: Idriss Jourdan, Rezi Sabashvili
"""

import sqlite3
from pathlib import Path
from flask import Flask, jsonify, request
from src.model import create_golem_model


class PopulationDatabase:
    """SQLite database for storing population history."""

    def __init__(self, db_path: str = "population_data.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table for population history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS population_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_step INTEGER NOT NULL,
                species TEXT NOT NULL,
                population REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table for species parameters
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS species_parameters (
                species TEXT PRIMARY KEY,
                growth_rate REAL NOT NULL,
                carrying_capacity REAL NOT NULL,
                initial_population REAL NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def save_step(self, time_step: int, populations: dict):
        """Save a simulation step to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for species, pop in populations.items():
            cursor.execute(
                """INSERT INTO population_history 
                   (time_step, species, population) 
                   VALUES (?, ?, ?)""",
                (time_step, species, pop)
            )

        conn.commit()
        conn.close()

    def get_history(self) -> list:
        """Get full history from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT time_step, species, population 
            FROM population_history 
            ORDER BY time_step, species
        """)
        rows = cursor.fetchall()
        conn.close()

        # Format data
        history = {}
        for time_step, species, pop in rows:
            if time_step not in history:
                history[time_step] = {"time": time_step, "populations": {}}
            history[time_step]["populations"][species] = pop

        return list(history.values())

    def save_species_params(self, species: str, growth_rate: float, 
                           carrying_capacity: float, initial_pop: float):
        """Save species parameters."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO species_parameters 
            (species, growth_rate, carrying_capacity, initial_population)
            VALUES (?, ?, ?, ?)
        """, (species, growth_rate, carrying_capacity, initial_pop))

        conn.commit()
        conn.close()

    def clear(self):
        """Clear all history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM population_history")
        conn.commit()
        conn.close()


# Initialize Flask app, model, and database
app = Flask(__name__)
model = create_golem_model()
db = PopulationDatabase()

# Save initial parameters to database
for name, species in model.species.items():
    db.save_species_params(
        name, 
        species.growth_rate, 
        species.carrying_capacity,
        species.size
    )


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "service": "Écosystème des Données - Golem API",
            "port": 16050,
            "group": "F",
            "database": Path(db.db_path).exists(),
        }
    ), 200


@app.route("/population/taille", methods=["GET"])
def get_population_size():
    """
    Get population size N_i for a species.
    
    Query Parameters:
        species (str): Species name (default: "Golem")
    
    Returns:
        JSON: {"taille": float, "species": str}
    """
    species = request.args.get("species", "Golem")

    if species not in model.species:
        return jsonify({"error": f"Species '{species}' not found"}), 404

    return jsonify(
        {
            "taille": model.species[species].size,
            "species": species,
        }
    ), 200


@app.route("/population/taux_de_croissance", methods=["GET"])
def get_growth_rate():
    """
    Get growth rate r_i for a species.
    
    Query Parameters:
        species (str): Species name (default: "Golem")
    
    Returns:
        JSON: {"taux_de_croissance": float, "species": str}
    """
    species = request.args.get("species", "Golem")

    if species not in model.species:
        return jsonify({"error": f"Species '{species}' not found"}), 404

    return jsonify(
        {
            "taux_de_croissance": model.species[species].growth_rate,
            "species": species,
        }
    ), 200


@app.route("/population/taux_de_competition", methods=["GET"])
def get_competition():
    """
    Get competition coefficient α_ij between two species.
    
    Query Parameters:
        species_i (str): First species (default: "Golem")
        species_j (str): Second species (default: "Human")
    
    Returns:
        JSON: {"taux_de_competition": float, "species_i": str, "species_j": str}
    """
    species_i = request.args.get("species_i", "Golem")
    species_j = request.args.get("species_j", "Human")

    if species_i not in model.species:
        return jsonify({"error": f"Species '{species_i}' not found"}), 404

    alpha = model.species[species_i].competition.get(species_j, 0.0)

    return jsonify(
        {
            "taux_de_competition": alpha,
            "species_i": species_i,
            "species_j": species_j,
        }
    ), 200


@app.route("/simulation/step", methods=["POST"])
def simulation_step():
    """
    Run one simulation step and save to database.
    
    Returns:
        JSON: {"success": bool, "time_step": int, "populations": dict}
    """
    new_sizes = model.step()
    
    # Save to database
    db.save_step(model.time_step, new_sizes)

    return jsonify(
        {
            "success": True,
            "time_step": model.time_step,
            "populations": new_sizes,
        }
    ), 200


@app.route("/simulation/state", methods=["GET"])
def get_state():
    """
    Get current simulation state.
    
    Returns:
        JSON: {"time_step": int, "populations": dict}
    """
    return jsonify(model.get_state()), 200


@app.route("/simulation/history", methods=["GET"])
def get_history():
    """
    Get full simulation history from database.
    
    Returns:
        JSON: {"history": list, "total_steps": int}
    """
    history = db.get_history()
    
    return jsonify(
        {
            "history": history,
            "total_steps": len(history),
        }
    ), 200


@app.route("/simulation/reset", methods=["POST"])
def reset_simulation():
    """
    Reset simulation to initial state and clear database.
    
    Returns:
        JSON: {"success": bool, "message": str}
    """
    # Reset model
    model.reset()
    
    # Restore initial populations
    for name in model.species:
        if name == "Golem":
            model.species[name].size = 100.0
        elif name == "Human":
            model.species[name].size = 150.0
    
    # Clear database
    db.clear()
    
    return jsonify(
        {
            "success": True, 
            "message": "Simulation reset successfully"
        }
    ), 200


@app.route("/database/stats", methods=["GET"])
def database_stats():
    """
    Get database statistics.
    
    Returns:
        JSON: Database info and statistics
    """
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    # Count records
    cursor.execute("SELECT COUNT(*) FROM population_history")
    total_records = cursor.fetchone()[0]
    
    # Get distinct time steps
    cursor.execute("SELECT COUNT(DISTINCT time_step) FROM population_history")
    total_steps = cursor.fetchone()[0]
    
    # Get species list
    cursor.execute("SELECT DISTINCT species FROM population_history")
    species_list = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify(
        {
            "database_path": db.db_path,
            "total_records": total_records,
            "total_steps": total_steps,
            "species": species_list,
            "database_size_bytes": Path(db.db_path).stat().st_size if Path(db.db_path).exists() else 0,
        }
    ), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error", "details": str(error)}), 500


if __name__ == "__main__":
    print("=" * 60)
    print("🧙 Écosystème des Données - Golem API")
    print("=" * 60)
    print(f"Port: 16050")
    print(f"Group: F")
    print(f"Database: {db.db_path}")
    print(f"Authors: Idriss Jourdan, Rezi Sabashvili")
    print("=" * 60)
    print("\nEndpoints:")
    print("  GET  /health")
    print("  GET  /population/taille")
    print("  GET  /population/taux_de_croissance")
    print("  GET  /population/taux_de_competition")
    print("  POST /simulation/step")
    print("  GET  /simulation/state")
    print("  GET  /simulation/history")
    print("  POST /simulation/reset")
    print("  GET  /database/stats")
    print("\n" + "=" * 60)
    
    app.run(host="0.0.0.0", port=16050, debug=True)
