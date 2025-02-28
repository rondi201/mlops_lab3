import os

from src.utils import load_ini_config

api_config = load_ini_config(os.getenv('API_CONFIG_FILE', 'settings.ini'), section='API')
