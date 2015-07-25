from flask_restful import Api, Resource
from flask_restful import fields, marshal, reqparse
from sqlalchemy import func
from serveza.login import current_user, login_required
from .base import api, swagger

BAR_BEER_FIELDS = {
    'beer_id': fields.Integer,
    'name': fields.String(attribute=lambda entry: entry.beer.name),
    'price': fields.String,
}

BAR_DETAILS_FIELDS = {
    'id': fields.Integer,
    'name': fields.String,
    'position': fields.FormattedString('{latitude}, {longitude}'),
    'address': fields.String,
    'carte': fields.List(fields.Nested(BAR_BEER_FIELDS)),
}

BAR_LIST_FIELDS = {
    'id': fields.Integer,
    'url': fields.Url('.bar_details'),
    'name': fields.String,
    'position': fields.FormattedString('{latitude}, {longitude}'),
}

class Bars(Resource):

    @swagger.operation()
    def get(self):
        from serveza.db import db
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
            bars = bars.filter(Bar.owners.contains(current_user._get_current_object()))

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


api.add_resource(Bars, '/bars')
api.add_resource(Bar, '/bars/<int:id>', endpoint='bar_details')
