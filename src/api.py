"""
REST API for Golem population simulation.
Port: 16050 (Group F)
"""

import sqlite3
from pathlib import Path
from flask import Flask, jsonify, request

# Import model (switch to model_with_api when ready)
from src.model import simulation_step, GROWTH_RATE, K, ALPHA


class PopulationDatabase:
    """SQLite database for population history."""
    
    def __init__(self, db_path: str = "population_data.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS population_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_step INTEGER NOT NULL,
                golem_population REAL NOT NULL,
                vampire_population REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_step(self, time_step: int, golem_pop: float, vampire_pop: float = None):
        """Save simulation step."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO population_history 
               (time_step, golem_population, vampire_population) 
               VALUES (?, ?, ?)""",
            (time_step, golem_pop, vampire_pop)
        )
        
        conn.commit()
        conn.close()
    
    def get_history(self) -> list:
        """Get full history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT time_step, golem_population, vampire_population 
            FROM population_history 
            ORDER BY time_step
        """)
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "time_step": row[0],
                "golem_population": row[1],
                "vampire_population": row[2]
            }
            for row in rows
        ]
    
    def clear(self):
        """Clear all history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM population_history")
        conn.commit()
        conn.close()


# Initialize Flask app
app = Flask(__name__)
db = PopulationDatabase()

# Simulation state
current_size = 100.0
time_step = 0


@app.route("/health", methods=["GET"])
def health():
    """Health check."""
    return jsonify({
        "status": "healthy",
        "service": "Golem Population API",
        "port": 16050,
        "group": "F",
        "database": Path(db.db_path).exists(),
    }), 200


@app.route("/population/taille", methods=["GET"])
def get_population_size():
    """
    Get current Golem population size.
    
    Returns:
        {"taille": float, "species": "Golem"}
    """
    return jsonify({
        "taille": current_size,
        "species": "Golem",
    }), 200


@app.route("/population/taux_de_croissance", methods=["GET"])
def get_growth_rate():
    """
    Get growth rate r.
    
    Returns:
        {"taux_de_croissance": float, "species": "Golem"}
    """
    return jsonify({
        "taux_de_croissance": GROWTH_RATE,
        "species": "Golem",
    }), 200


@app.route("/population/taux_de_competition", methods=["GET"])
def get_competition():
    """
    Get competition coefficient α.
    
    Returns:
        {"taux_de_competition": float, "species_i": "Golem", "species_j": "Vampire"}
    """
    return jsonify({
        "taux_de_competition": ALPHA,
        "species_i": "Golem",
        "species_j": "Vampire",
    }), 200


@app.route("/simulation/step", methods=["POST"])
def simulation_step_endpoint():
    """
    Execute one simulation step.
    
    Returns:
        {"success": bool, "time_step": int, "golem_population": float, "vampire_population": float}
    """
    global current_size, time_step
    
    result = simulation_step(current_size)
    current_size = result["taille"]
    time_step += 1
    
    # Save to database
    db.save_step(time_step, current_size, result.get("vampire"))
    
    return jsonify({
        "success": True,
        "time_step": time_step,
        "golem_population": current_size,
        "vampire_population": result.get("vampire"),
    }), 200


@app.route("/simulation/state", methods=["GET"])
def get_state():
    """
    Get current simulation state.
    
    Returns:
        {"time_step": int, "golem_population": float}
    """
    return jsonify({
        "time_step": time_step,
        "golem_population": current_size,
    }), 200


@app.route("/simulation/history", methods=["GET"])
def get_history():
    """
    Get full simulation history.
    
    Returns:
        {"history": list, "total_steps": int}
    """
    history = db.get_history()
    return jsonify({
        "history": history,
        "total_steps": len(history),
    }), 200


@app.route("/simulation/reset", methods=["POST"])
def reset_simulation():
    """
    Reset simulation to initial state.
    
    Returns:
        {"success": bool, "message": str}
    """
    global current_size, time_step
    
    current_size = 100.0
    time_step = 0
    db.clear()
    
    return jsonify({
        "success": True,
        "message": "Simulation reset successfully"
    }), 200


@app.route("/database/stats", methods=["GET"])
def database_stats():
    """
    Get database statistics.
    
    Returns:
        {"database_path": str, "total_records": int, "database_size_bytes": int}
    """
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM population_history")
    total_records = cursor.fetchone()[0]
    
    conn.close()
    
    db_path = Path(db.db_path)
    db_size = db_path.stat().st_size if db_path.exists() else 0
    
    return jsonify({
        "database_path": db.db_path,
        "total_records": total_records,
        "database_size_bytes": db_size,
    }), 200


if __name__ == "__main__":
    print("=" * 60)
    print("🧙 Golem Population API - Group F")
    print("=" * 60)
    print(f"Port: 16050")
    print(f"Database: {db.db_path}")
    print(f"Model: Test mode (Vampire = K * cos(t))")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=16050, debug=True)
