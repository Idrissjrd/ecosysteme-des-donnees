"""
Database module for storing population history.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict


class PopulationDatabase:
    """SQLite database for population data."""

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
                species TEXT NOT NULL,
                population REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def save_step(self, time_step: int, populations: Dict[str, float]):
        """Save a simulation step to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for species, pop in populations.items():
            cursor.execute(
                "INSERT INTO population_history (time_step, species, population) VALUES (?, ?, ?)",
                (time_step, species, pop)
            )

        conn.commit()
        conn.close()

    def get_history(self) -> List[Dict]:
        """Get full history from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT time_step, species, population FROM population_history ORDER BY time_step"
        )
        rows = cursor.fetchall()
        conn.close()

        # Format data
        history = {}
        for time_step, species, pop in rows:
            if time_step not in history:
                history[time_step] = {"time": time_step, "populations": {}}
            history[time_step]["populations"][species] = pop

        return list(history.values())

    def clear(self):
        """Clear all history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM population_history")
        conn.commit()
        conn.close()
