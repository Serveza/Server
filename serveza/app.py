from flask import Flask
from flask import render_template
from flask_cors import CORS
from flask_debugtoolbar import DebugToolbarExtension
from .api import api_blueprint
from .db import db

app = Flask(__name__)
app.config.from_object('serveza.settings')

toolbar = DebugToolbarExtension(app)
cors = CORS(app)

# Init DB
db.init_app(app)

# Init modules
app.register_blueprint(api_blueprint, url_prefix='/api')
