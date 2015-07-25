from flask import Blueprint
from flask_restful import Api
from flask_restful_swagger import swagger

api_blueprint = Blueprint('api', __name__)

api = Api(api_blueprint)
api = swagger.docs(api, apiVersion='0.1', api_spec_url='/spec')
