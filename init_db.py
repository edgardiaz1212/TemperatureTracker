# c:\Users\AdminLocal\Documents\Github\TemperatureTracker\init_db.py
from dotenv import load_dotenv
import os

# Cargar variables de entorno FIRST
load_dotenv()

# Verificar que existe la variable de entorno DATABASE_URL BEFORE importing database
database_url_env = os.environ.get('DATABASE_URL')
if not database_url_env:
    print("Error: DATABASE_URL no está configurada en el archivo .env o en el entorno del sistema.")
    exit(1)

# Now that we know DATABASE_URL is likely set, import the database module
from database import init_db

if __name__ == "__main__":
    print("Inicializando base de datos...")
    # init_db() will use the engine created using the loaded DATABASE_URL
    init_db()
    print("Base de datos inicializada correctamente.")

