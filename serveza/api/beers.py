from flask_restful import Resource
from flask_restful import fields, marshal, reqparse
from .base import api, swagger

BEER_LIST_FIELDS = {
    'id': fields.Integer,
    'url': fields.Url('.beer_details'),
    'name': fields.String,
}

BEER_DETAILS_FIELDS = {
    'id': fields.Integer,
    'url': fields.Url('.beer_details'),
    'name': fields.String,
    'image': fields.String,
    'description': fields.String,
    'brewery': fields.String,
    'degree': fields.Float,
}

class Beers(Resource):

    @swagger.operation()
    def get(self):
        from serveza.db import Beer

        beers = Beer.query.all()
        return marshal(beers, BEER_LIST_FIELDS)


class Beer(Resource):

    @swagger.operation()
    def get(self, id):
        from serveza.db import Beer

        beer = Beer.query.get(id)
        return marshal(beer, BEER_DETAILS_FIELDS)


api.add_resource(Beers, '/beers')
api.add_resource(Beer, '/beers/<int:id>', endpoint='beer_details')
