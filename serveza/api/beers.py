from flask import abort
from flask_restful import Resource
from flask_restful import fields, marshal, reqparse
from serveza.db import db
from serveza.login import get_user, login_required, api_token_param
from .base import api, swagger
from .fields import BEER_LIST_FIELDS, BEER_DETAILS_FIELDS, BEER_COMMENT_FIELDS


class Beers(Resource):

    @swagger.operation()
    def get(self):
        from serveza.db import Beer

        beers = Beer.query.all()
        return marshal(beers, BEER_LIST_FIELDS)

    @swagger.operation(
        parameters=[
            dict(api_token_param, paramType='form'),
            dict(name='name', type='string', description='Beer name', required=True, paramType='form'),
        ],
    )
    @login_required
    def post(self):
        from serveza.db import Beer
        from serveza.utils.scrap.beer import scrap_beer

        parser = reqparse.RequestParser()
        parser.add_argument('name', required=True)
        args = parser.parse_args()

        try:
            beer = scrap_beer(args.name)
        except:
            beer = scrap_beer('%s (bière)' % (args.name))

        if beer is None:
            abort(404, 'Can\'t find informations about this beer.')

        _beer = Beer.query.filter(Beer.name == beer.name).first()
        if _beer is not None:
            beer = _beer

        db.session.add(beer)
        db.session.commit()

        return marshal(beer, BEER_DETAILS_FIELDS, envelope='beer')


class Beer(Resource):

    @swagger.operation()
    def get(self, id):
        from serveza.db import Beer

        beer = Beer.query.get_or_404(id)
        return marshal(beer, BEER_DETAILS_FIELDS)


class BeerComments(Resource):

    @swagger.operation()
    def get(self, id):
        from serveza.db import Beer

        beers = Beer.query.get_or_404(id)
        return marshal(beers.comments, BEER_COMMENT_FIELDS, envelope='comments')

    @swagger.operation()
    @login_required
    def post(self, id):
        from serveza.db import Beer, BeerComment

        beer = Beer.query.get_or_404(id)

        parser = reqparse.RequestParser()
        parser.add_argument('score', type=int)
        parser.add_argument('comment')
        args = parser.parse_args()

        author = get_user()

        comment = BeerComment(
            beer=beer, author=author, score=args.score, comment=args.comment)

        try:
            beer.comments.append(comment)
            db.session.add(beer)
            db.session.commit()
        except:
            db.session.rollback()

        return marshal(comment, BEER_COMMENT_FIELDS, envelope='comment')


api.add_resource(Beers, '/beers')
api.add_resource(Beer, '/beers/<int:id>', endpoint='beer_details')
api.add_resource(
    BeerComments, '/beers/<int:id>/comments', endpoint='beer_comments')
