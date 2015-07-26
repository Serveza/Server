from flask import url_for
from flask_restful import Resource
from flask_restful import fields, marshal, reqparse
from sqlalchemy import func
from serveza.db import db
from serveza.login import current_user, login_required
from .base import api, swagger
from .fields import BAR_BEER_FIELDS, BAR_COMMENT_FIELDS, BAR_DETAILS_FIELDS, BAR_LIST_FIELDS


class Bars(Resource):

    @swagger.operation()
    def get(self):
        from serveza.db import Bar, BarBeer, Beer

        m_fields = BAR_LIST_FIELDS.copy()

        position = lambda value: tuple(map(float, value.split(',')))

        parser = reqparse.RequestParser()
        parser.add_argument('latitude', type=float)
        parser.add_argument('longitude', type=float)
        parser.add_argument('pos', type=position)
        parser.add_argument('range', type=float)
        parser.add_argument('beers', action='append', type=int, default=[])
        parser.add_argument('owned', type=bool, default=False)
        args = parser.parse_args()

        latitude = args.latitude
        longitude = args.longitude

        pos = (latitude, longitude)
        if args.pos:
            pos = args.pos

        bars = Bar.query

        if args.owned and current_user:
            bars = bars.filter(Bar.owner == current_user._get_current_object())

        if all(p is not None for p in pos):
            bars = bars.order_by(Bar.distance(pos))

            m_fields['distance'] = fields.Float(
                attribute=lambda bar: bar.distance(pos))

            if args.range is not None:
                bars = bars.filter(Bar.distance(pos) <= args.range)

        if len(args.beers) > 0:
            q = BarBeer.query\
                        .with_entities(BarBeer.bar_id, func.count('*').label('count'))\
                        .filter(BarBeer.beer_id.in_(args.beers))\
                        .group_by(BarBeer.bar_id)\
                        .subquery()
            bars = bars.outerjoin((q, Bar.id == q.c.bar_id))\
                        .filter(q.c.count >= len(args.beers))

        bars = bars.all()
        return marshal(bars, m_fields, envelope='bars')

    @swagger.operation()
    @login_required
    def post(self):
        pass


class Bar(Resource):

    @swagger.operation()
    def get(self, id):
        from serveza.db import Bar

        bar = Bar.query.get(id)
        return marshal(bar, BAR_DETAILS_FIELDS, envelope='bar')


class BarComments(Resource):

    @swagger.operation()
    def get(self, id):
        from serveza.db import Bar

        bar = Bar.query.get(id)
        return marshal(bar.comments, BAR_COMMENT_FIELDS, envelope='comments')

    @swagger.operation()
    @login_required
    def post(self, id):
        from serveza.db import Bar, BarComment

        bar = Bar.query.get(id)

        parser = reqparse.RequestParser()
        parser.add_argument('score', type=int)
        parser.add_argument('comment')
        args = parser.parse_args()

        comment = BarComment(author=current_user, score=args.score, comment=args.comment)
        bar.comments.append(comment)

        db.session.add(bar)
        db.session.commit()

        return marshal(comment, BAR_COMMENT_FIELDS, envelope='comment')

api.add_resource(Bars, '/bars')
api.add_resource(Bar, '/bars/<int:id>', endpoint='bar_details')
api.add_resource(BarComments, '/bars/<int:id>/comments', endpoint='bar_comments')
