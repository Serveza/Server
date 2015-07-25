from flask import Flask

app = Flask(__name__)
app.config.from_object('serveza.settings')

# Init debug toolbar
from flask_debugtoolbar import DebugToolbarExtension
toolbar = DebugToolbarExtension(app)

# Init CORS
from flask_cors import CORS
cors = CORS(app, resources=r'/api/*')

# Init DB
from .db import db
db.init_app(app)

# Init modules
from .api import api_blueprint
app.register_blueprint(api_blueprint, url_prefix='/api')
