from flask_restful import Resource
from flask_restful import fields, marshal, reqparse
from serveza.login import get_user, login_required
from .base import api, swagger
from .fields import BEER_LIST_FIELDS, BEER_DETAILS_FIELDS, BEER_COMMENT_FIELDS


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
