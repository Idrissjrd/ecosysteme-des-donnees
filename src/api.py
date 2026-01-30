"""
REST API for Golem population simulation.
Port: 16050 (Group F)
"""

from flask import Flask, jsonify, request
from pathlib import Path

# --- IMPORTS ---
from src.model import simulation_step, GROWTH_RATE, K, ALPHA
from src.database import PopulationDatabase

# Initialize Flask app & Database
app = Flask(__name__)
db = PopulationDatabase()

# --- STATE MANAGEMENT ---
# Load the last state from DB so we don't reset on restart
history = db.get_history()
if history:
    last_record = history[-1]
    time_step = last_record.get("time", 0)
    pops = last_record.get("populations", {})
    current_size = pops.get("Golem", 100.0)
    print(f"♻️ System recovered: Time={time_step}, Size={current_size:.1f}")
else:
    current_size = 100.0
    time_step = 0

# NEW: Global variable to track connection status
is_connected = False


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "Golem Population API",
        "port": 16050,
        "group": "F",
        "history_len": len(db.get_history())
    }), 200





# --- REQUIRED ENDPOINTS ---

@app.route("/taille", methods=["GET"])
@app.route("/population/taille", methods=["GET"])
def get_population_size():
    return jsonify({
        "taille": current_size,
        "species": "Golem",
    }), 200

@app.route("/taux_de_croissance", methods=["GET"])
@app.route("/population/taux_de_croissance", methods=["GET"])
def get_growth_rate():
    return jsonify({
        "taux_de_croissance": GROWTH_RATE,
        "species": "Golem",
    }), 200

@app.route("/taux_de_competition", methods=["GET"])
@app.route("/population/taux_de_competition", methods=["GET"])
def get_competition():
    return jsonify({
        "taux_de_competition": ALPHA,
        "species_i": "Golem",
        "species_j": "Vampire",
    }), 200


# --- SIMULATION ENDPOINTS ---

@app.route("/simulation/step", methods=["POST"])
def simulation_step_endpoint():
    global current_size, time_step, is_connected
    
    # 1. Run Logic
    # result contains: {'taille': ..., 'vampire': ..., 'connected': ...}
    result = simulation_step(current_size)
    
    current_size = result["taille"]
    vampire_pop = result.get("vampire", 0.0)
    
    # FIX 1: Capture the connection status from the model
    is_connected = result.get("connected", False)
    
    time_step += 1
    
    # 2. Save to Database
    db.save_step(
        time_step, 
        {
            "Golem": current_size,
            "Vampire": vampire_pop
        }
    )
    
    return jsonify({
        "success": True,
        "time_step": time_step,
        "taille": current_size,
        "vampire": vampire_pop,
        "connected": is_connected  # Send status back
    }), 200


@app.route("/simulation/state", methods=["GET"])
def get_state():
    """
    Returns current state. Now includes 'connected' for the Dashboard!
    """
    return jsonify({
        "time_step": time_step,
        "taille": current_size,
        # Helper 'populations' dict for dashboard compatibility
        "populations": {
            "Golem": current_size,
            "Vampire": 0 # Dashboard fetches history for real data
        },
        # FIX 2: Send the global connection status to the frontend
        "connected": is_connected  
    }), 200


@app.route("/simulation/history", methods=["GET"])
def get_history_endpoint():
    history_data = db.get_history()
    return jsonify({
        "history": history_data,
        "total_steps": len(history_data),
    }), 200


@app.route("/simulation/reset", methods=["POST"])
def reset_simulation():
    global current_size, time_step, is_connected
    current_size = 100.0
    time_step = 0
    is_connected = False
    db.clear()
    return jsonify({"success": True, "message": "Reset done"}), 200


@app.route("/database/stats", methods=["GET"])
def database_stats():
    return jsonify({
        "database_path": db.db_path,
        "records": len(db.get_history())
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=16050, debug=True)