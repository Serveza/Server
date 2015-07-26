from flask import url_for
from flask_restful import Resource
from flask_restful import fields, marshal, reqparse
from sqlalchemy import func
from serveza.db import db
from serveza.login import current_user, get_user, login_required, api_token_param
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

    @swagger.operation(
        parameters=[
            dict(api_token_param, paramType='form'),
            dict(name='name', type='string', description='Bar name',
                 required=True, paramType='form'),
            dict(name='image', type='url',
                 description='Bar photo', paramType='form'),
            dict(name='website', type='url',
                 description='Bar website', paramType='form'),
            dict(name='position', type='string',
                 description='Bar location', paramType='form'),
        ],
    )
    @login_required
    def post(self):
        from serveza.db import Bar

        parser = reqparse.RequestParser()
        parser.add_argument('name', required=True)
        parser.add_argument('image')
        parser.add_argument('website')
        parser.add_argument('position')
        args = parser.parse_args()

        bar = Bar(name=args.name, owner=current_user)
        bar.image = args.image
        bar.website = args.website
        bar.position = args.position

        _bar = Bar.query.filter(Bar.name == bar.name, Bar.latitude == bar.latitude, Bar.longitude == bar.longitude).first()
        if _bar is not None:
            bar = _bar

        db.session.add(bar)
        db.session.commit()

        return marshal(bar, BAR_DETAILS_FIELDS, envelope='bar')


class Bar(Resource):

    @swagger.operation()
    def get(self, id):
        from serveza.db import Bar

        bar = Bar.query.get_or_404(id)
        return marshal(bar, BAR_DETAILS_FIELDS, envelope='bar')

    @swagger.operation(
        parameters=[
            dict(api_token_param, paramType='form'),
            dict(name='name', type='string', description='Bar name',
                 required=True, paramType='form'),
            dict(name='image', type='url',
                 description='Bar photo', paramType='form'),
            dict(name='website', type='url',
                 description='Bar website', paramType='form'),
            dict(name='position', type='string',
                 description='Bar location', paramType='form'),
        ],
    )
    @login_required
    def put(self, id):
        from serveza.db import Bar

        parser = reqparse.RequestParser()
        parser.add_argument('name')
        parser.add_argument('image')
        parser.add_argument('website')
        parser.add_argument('position')
        args = parser.parse_args()

        bar = Bar.query.get_or_404(id)
        if args.name:
            bar.name = args.name
        if args.image:
            bar.image = args.image
        if args.website:
            bar.website = args.website
        if args.position:
            bar.position = args.position

        db.session.add(bar)
        db.session.commit()

        return 'ok'


class BarComments(Resource):

    @swagger.operation()
    def get(self, id):
        from serveza.db import Bar

        bar = Bar.query.get_or_404(id)
        return marshal(bar.comments, BAR_COMMENT_FIELDS, envelope='comments')

    @swagger.operation(
        parameters=[
            dict(api_token_param, paramType='form'),
            dict(name='score', type='int',
                 description='Score', paramType='form'),
            dict(name='comment', type='text',
                 description='Score', paramType='form'),
        ],
    )
    @login_required
    def post(self, id):
        from serveza.db import Bar, BarComment

        bar = Bar.query.get_or_404(id)

        parser = reqparse.RequestParser()
        parser.add_argument('score', type=int)
        parser.add_argument('comment')
        args = parser.parse_args()

        author = get_user()

        comment = BarComment(
            bar=bar, author=author, score=args.score, comment=args.comment)

        try:
            bar.comments.append(comment)
            db.session.add(bar)
            db.session.commit()
        except:
            db.session.rollback()

        return marshal(comment, BAR_COMMENT_FIELDS, envelope='comment')

api.add_resource(Bars, '/bars')
api.add_resource(Bar, '/bars/<int:id>', endpoint='bar_details')
api.add_resource(
    BarComments, '/bars/<int:id>/comments', endpoint='bar_comments')
