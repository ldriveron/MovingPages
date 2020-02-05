from flask import Flask
from flask_talisman import Talisman

app = Flask(__name__)
app._static_folder = "static"  # set a static files folder for Flask app
Talisman(app)

from app_files import routes  # import the routes python file
