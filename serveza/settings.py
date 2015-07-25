from geopy.geocoders import Nominatim
from pathlib import Path

PROJECT_ROOT = Path().parent.resolve()

# Database config
DB_PATH = PROJECT_ROOT / 'db.sqlite3'
SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % (DB_PATH)

PASSWORD_SCHEMES = [
    'pbkdf2_sha512',
]

SQLALCHEMY_ECHO = True

# Session
SECRET_KEY = 'GIBJV@y<I2@jfrEBFBx@*7`l9:@@ax~v'

DEBUG_TB_ENABLED = True

# Geo
GEOLOCATOR = Nominatim()
