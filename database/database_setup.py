import sqlite3
import os

# Define la ruta de la base de datos dentro de la carpeta 'database'
DB_FOLDER = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_FOLDER, "disc_insight.db")

# --- Sentencias SQL para crear la estructura ---
SQL_CREATE_SCRIPT = """
--
-- Tabla: cases
-- Almacena la información general de cada persona o caso.
--
CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    alias TEXT,
    tags TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TRIGGER IF NOT EXISTS trigger_cases_updated_at
AFTER UPDATE ON cases
FOR EACH ROW
BEGIN
    UPDATE cases SET updated_at = datetime('now', 'localtime') WHERE id = OLD.id;
END;

--
-- Tabla: inputs
-- Registra cada dato de entrada (texto, ruta de imagen, HTML).
--
CREATE TABLE IF NOT EXISTS inputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    input_type TEXT NOT NULL CHECK(input_type IN ('text', 'image', 'html')),
    content TEXT NOT NULL,
    gemini_raw_response TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE
);

--
-- Tabla: disc_evaluations
-- Guarda el historial de valoraciones DISC consolidadas para un caso.
--
CREATE TABLE IF NOT EXISTS disc_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    disc_d REAL NOT NULL CHECK(disc_d BETWEEN 0 AND 100),
    disc_i REAL NOT NULL CHECK(disc_i BETWEEN 0 AND 100),
    disc_s REAL NOT NULL CHECK(disc_s BETWEEN 0 AND 100),
    disc_c REAL NOT NULL CHECK(disc_c BETWEEN 0 AND 100),
    confidence REAL NOT NULL CHECK(confidence BETWEEN 0 AND 100),
    justification_text TEXT,
    is_manual_override INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE
);

--
-- Tabla: strategies
-- Contiene las estrategias definidas para abordar un caso.
--
CREATE TABLE IF NOT EXISTS strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    objective TEXT,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'paused', 'completed')),
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE
);

CREATE TRIGGER IF NOT EXISTS trigger_strategies_updated_at
AFTER UPDATE ON strategies
FOR EACH ROW
BEGIN
    UPDATE strategies SET updated_at = datetime('now', 'localtime') WHERE id = OLD.id;
END;

--
-- Tabla: strategy_events
-- Registra notas, resultados y sugerencias de Gemini asociadas a una estrategia.
--
CREATE TABLE IF NOT EXISTS strategy_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL,
    event_type TEXT NOT NULL DEFAULT 'user_note' CHECK(event_type IN ('user_note', 'gemini_suggestion')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (strategy_id) REFERENCES strategies (id) ON DELETE CASCADE
);

--
-- Tabla: settings
-- Almacena la configuración de la aplicación.
--
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY NOT NULL,
    value TEXT NOT NULL
);

-- Insertar valores por defecto para la configuración inicial (si no existen)
INSERT OR IGNORE INTO settings (key, value) VALUES
('gemini_api_key', ''),
('weight_image', '0.3'),
('weight_html', '0.5'),
('weight_text', '0.2');
"""

def setup_database():
    """Crea y configura la base de datos si no existe."""
    conn = None
    try:
        print(f"Conectando y configurando la base de datos en: {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Habilitar soporte para claves foráneas (importante para ON DELETE CASCADE)
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Ejecutar todo el script de creación de tablas
        cursor.executescript(SQL_CREATE_SCRIPT)
        
        conn.commit()
        print("Base de datos configurada exitosamente.")
        
    except sqlite3.Error as e:
        print(f"Error al configurar la base de datos: {e}")
    finally:
        if conn:
            conn.close()
            print("Conexión a la base de datos cerrada.")

if __name__ == "__main__":
    setup_database()
