import sqlite3
import os
from typing import List, Dict, Any, Optional

# Construir la ruta a la base de datos de forma robusta
# Se asume que este archivo está en 'app/core/', y la BD en 'database/'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "database", "disc_insight.db")

class DatabaseManager:
    """
    Singleton class to manage the database connection and operations.
    This ensures only one connection is active throughout the application's lifecycle.
    """
    _instance = None

    @staticmethod
    def get_instance():
        """Static access method."""
        if DatabaseManager._instance is None:
            DatabaseManager()
        return DatabaseManager._instance

    def __init__(self):
        """Virtually private constructor."""
        if DatabaseManager._instance is not None:
            raise Exception("This class is a singleton! Use get_instance().")
        else:
            self.conn = None
            self.connect()
            DatabaseManager._instance = self

    def connect(self):
        """Establishes connection to the SQLite database."""
        try:
            self.conn = sqlite3.connect(DB_PATH)
            # Row factory para obtener resultados como diccionarios en lugar de tuplas
            self.conn.row_factory = sqlite3.Row 
            # Habilitar claves foráneas
            self.conn.execute("PRAGMA foreign_keys = ON;")
            print("Database connection successful.")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            self.conn = None

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            print("Database connection closed.")

    # --- CRUD Operations for 'cases' table ---

    def create_case(self, name: str, alias: str = "", tags: str = "", notes: str = "") -> Optional[int]:
        """
        Creates a new case in the database.
        Returns the ID of the newly created case, or None on failure.
        """
        sql = """
        INSERT INTO cases (name, alias, tags, notes)
        VALUES (?, ?, ?, ?)
        """
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(sql, (name, alias, tags, notes))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error creating case: {e}")
            return None

    def get_case_by_id(self, case_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single case by its ID.
        Returns a dictionary representing the case, or None if not found.
        """
        sql = "SELECT * FROM cases WHERE id = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (case_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Error fetching case {case_id}: {e}")
            return None

    def get_all_cases(self) -> List[Dict[str, Any]]:
        """
        Retrieves all cases from the database, ordered by the most recently updated.
        Returns a list of dictionaries, where each dictionary represents a case.
        """
        sql = "SELECT * FROM cases ORDER BY updated_at DESC"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            # Convert sqlite3.Row objects to standard dictionaries
            cases = [dict(row) for row in cursor.fetchall()]
            return cases
        except sqlite3.Error as e:
            print(f"Error fetching cases: {e}")
            return []

    def update_case(self, case_id: int, name: str, alias: str, tags: str, notes: str) -> bool:
        """
        Updates an existing case.
        The 'updated_at' field is handled automatically by the database trigger.
        Returns True on success, False on failure.
        """
        sql = """
        UPDATE cases
        SET name = ?, alias = ?, tags = ?, notes = ?
        WHERE id = ?
        """
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(sql, (name, alias, tags, notes, case_id))
                return True
        except sqlite3.Error as e:
            print(f"Error updating case {case_id}: {e}")
            return False

    def delete_case(self, case_id: int) -> bool:
        """
        Deletes a case and all its related data (inputs, evaluations, etc.)
        due to 'ON DELETE CASCADE' constraint.
        Returns True on success, False on failure.
        """
        sql = "DELETE FROM cases WHERE id = ?"
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(sql, (case_id,))
                return True
        except sqlite3.Error as e:
            print(f"Error deleting case {case_id}: {e}")
            return False

    def create_input(self, case_id: int, input_type: str, content: str) -> Optional[int]:
        """
        Creates a new input record associated with a case.
        Returns the ID of the new input, or None on failure.
        """
        sql = """
        INSERT INTO inputs (case_id, input_type, content)
        VALUES (?, ?, ?)
        """
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(sql, (case_id, input_type, content))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error creating input for case {case_id}: {e}")
            return None

    def get_inputs_for_case(self, case_id: int) -> List[Dict[str, Any]]:
        """
        Retrieves all inputs for a specific case, ordered by creation date.
        """
        sql = "SELECT * FROM inputs WHERE case_id = ? ORDER BY created_at DESC"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (case_id,))
            inputs = [dict(row) for row in cursor.fetchall()]
            return inputs
        except sqlite3.Error as e:
            print(f"Error fetching inputs for case {case_id}: {e}")
            return []

    def get_setting(self, key: str) -> Optional[str]:
        """
        Retrieves a specific setting value by its key.
        """
        sql = "SELECT value FROM settings WHERE key = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (key,))
            row = cursor.fetchone()
            return row['value'] if row else None
        except sqlite3.Error as e:
            print(f"Error getting setting {key}: {e}")
            return None

    def get_latest_evaluation_for_case(self, case_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves the most recent DISC evaluation for a given case.
        """
        sql = """
        SELECT * FROM disc_evaluations 
        WHERE case_id = ? 
        ORDER BY version_number DESC 
        LIMIT 1
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (case_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Error fetching latest evaluation for case {case_id}: {e}")
            return None

    def update_setting(self, key: str, value: str) -> bool:
        """
        Updates or inserts a setting value.
        """
        sql = "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)"
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(sql, (key, value))
                return True
        except sqlite3.Error as e:
            print(f"Error updating setting {key}: {e}")
            return False

    def update_input_with_gemini_response(self, input_id: int, response: str) -> bool:
        """Updates an input record with the raw JSON response from Gemini."""
        sql = "UPDATE inputs SET gemini_raw_response = ? WHERE id = ?"
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(sql, (response, input_id))
                return True
        except sqlite3.Error as e:
            print(f"Error updating input {input_id} with Gemini response: {e}")
            return False

    def get_latest_evaluation_version(self, case_id: int) -> int:
        """Gets the highest version number for a case's evaluations."""
        sql = "SELECT MAX(version_number) FROM disc_evaluations WHERE case_id = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (case_id,))
            result = cursor.fetchone()[0]
            return result if result is not None else 0
        except sqlite3.Error as e:
            print(f"Error getting latest version for case {case_id}: {e}")
            return 0

    def create_disc_evaluation(self, case_id: int, version: int, d: float, i: float, s: float, c: float, confidence: float, justification: str) -> Optional[int]:
        """Creates a new consolidated DISC evaluation record."""
        sql = """
        INSERT INTO disc_evaluations 
        (case_id, version_number, disc_d, disc_i, disc_s, disc_c, confidence, justification_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(sql, (case_id, version, d, i, s, c, confidence, justification))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error creating DISC evaluation for case {case_id}: {e}")
            return None

    def create_strategy(self, case_id: int, title: str, objective: str, description: str, status: str) -> Optional[int]:
        sql = "INSERT INTO strategies (case_id, title, objective, description, status) VALUES (?, ?, ?, ?, ?)"
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(sql, (case_id, title, objective, description, status))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error creating strategy: {e}")
            return None

    def get_strategies_for_case(self, case_id: int) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM strategies WHERE case_id = ? ORDER BY created_at DESC"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (case_id,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error getting strategies for case {case_id}: {e}")
            return []

    def update_strategy(self, strategy_id: int, title: str, objective: str, description: str, status: str) -> bool:
        sql = "UPDATE strategies SET title = ?, objective = ?, description = ?, status = ? WHERE id = ?"
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(sql, (title, objective, description, status, strategy_id))
                return True
        except sqlite3.Error as e:
            print(f"Error updating strategy {strategy_id}: {e}")
            return False

    # --- CRUD for 'strategy_events' ---

    def create_strategy_event(self, strategy_id: int, event_type: str, content: str) -> Optional[int]:
        sql = "INSERT INTO strategy_events (strategy_id, event_type, content) VALUES (?, ?, ?)"
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(sql, (strategy_id, event_type, content))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error creating strategy event: {e}")
            return None

    def get_events_for_strategy(self, strategy_id: int) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM strategy_events WHERE strategy_id = ? ORDER BY created_at ASC"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (strategy_id,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error getting events for strategy {strategy_id}: {e}")
            return []


# --- Bloque de prueba para verificar la funcionalidad del módulo ---
if __name__ == '__main__':
    print("--- Running DatabaseManager tests ---")
    db_manager = DatabaseManager.get_instance()

    if db_manager.conn is None:
        print("Could not connect to the database. Aborting tests.")
    else:
        # 1. Crear casos
        print("\n1. Creating new cases...")
        case1_id = db_manager.create_case("John Doe", "JD", "sales, prospect", "First meeting notes.")
        case2_id = db_manager.create_case("Jane Smith", "JS", "engineering, candidate", "Technical interview notes.")
        print(f"Created case with ID: {case1_id}")
        print(f"Created case with ID: {case2_id}")

        # 2. Obtener todos los casos
        print("\n2. Getting all cases...")
        all_cases = db_manager.get_all_cases()
        for case in all_cases:
            print(f"  - ID: {case['id']}, Name: {case['name']}, Tags: {case['tags']}")

        # 3. Actualizar un caso
        if case1_id:
            print(f"\n3. Updating case {case1_id}...")
            success = db_manager.update_case(case1_id, "Johnathan 'John' Doe", "Johnny", "sales, key-account", "Updated notes.")
            print(f"Update successful: {success}")
            updated_cases = db_manager.get_all_cases()
            print("Cases after update:")
            for case in updated_cases:
                print(f"  - ID: {case['id']}, Name: {case['name']}, Alias: {case['alias']}")

        # 4. Eliminar un caso
        if case2_id:
            print(f"\n4. Deleting case {case2_id}...")
            success = db_manager.delete_case(case2_id)
            print(f"Deletion successful: {success}")
            final_cases = db_manager.get_all_cases()
            print("Final list of cases:")
            for case in final_cases:
                print(f"  - ID: {case['id']}, Name: {case['name']}")

        # Cerrar la conexión
        db_manager.close()
