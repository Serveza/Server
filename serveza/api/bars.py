import arrow
from flask import abort, url_for, jsonify
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

        owner = get_user()

        bar = Bar(name=args.name, owner=owner)
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

    @swagger.operation(
        parameters=[
            dict(api_token_param, paramType='form'),
        ],
    )
    @login_required
    def delete(self, id):
        from serveza.db import Bar

        bar = Bar.query.get_or_404(id)
        db.session.delete(bar)
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


class BarBeers(Resource):

    @swagger.operation()
    def get(self, id):
        from serveza.db import Bar

        bar = Bar.query.get_or_404(id)
        return marshal(bar.carte, BAR_BEER_FIELDS, envelope='beers')

    @swagger.operation(
        parameters=[
            dict(api_token_param, paramType='form'),
            dict(name='beer', type='int', description='Beer ID', required=True, paramType='form'),
            dict(name='price', type='string', description='Beer price', required=True, paramType='form'),
        ],
    )
    @login_required
    def post(self, id):
        from serveza.db import Bar, BarBeer, Beer

        bar = Bar.query.get_or_404(id)

        def price(s):
            from money import Money

            parts = s.split()
            if len(parts) != 2:
                raise ValueError('The price must be in format: <amount> <currency>')
            (amount, currency) = parts
            return Money(amount, currency)

        parser = reqparse.RequestParser()
        parser.add_argument('beer', type=int, required=True)
        parser.add_argument('price', type=price, required=True)
        args = parser.parse_args()

        beer = Beer.query.get_or_404(args.beer)

        entry = BarBeer(bar=bar, beer=beer, price=args.price)
        db.session.add(entry)
        db.session.commit()

        return marshal(entry, BAR_BEER_FIELDS, envelope='beer')

    @swagger.operation(
        parameters=[
            dict(api_token_param, paramType='form'),
            dict(name='beer', type='int', description='Beer ID', required=True, paramType='form'),
            dict(name='price', type='string', description='Beer price', required=True, paramType='form'),
        ],
    )
    @login_required
    def put(self, id):
        from serveza.db import Bar, BarBeer, Beer

        bar = Bar.query.get_or_404(id)

        def price(s):
            from money import Money

            parts = s.split()
            if len(parts) != 2:
                raise ValueError('The price must be in format: <amount> <currency>')
            (amount, currency) = parts
            return Money(amount, currency)

        parser = reqparse.RequestParser()
        parser.add_argument('beer', type=int, required=True)
        parser.add_argument('price', type=price, required=True)
        args = parser.parse_args()

        beer = Beer.query.get_or_404(args.beer)

        entry = BarBeer.query.filter(BarBeer.bar == bar, BarBeer.beer == beer).first()
        if entry is None:
            abort(404)
        entry.price = args.price
        db.session.add(entry)
        db.session.commit()

        return marshal(entry, BAR_BEER_FIELDS, envelope='beer')

    @swagger.operation(
        parameters=[
            dict(api_token_param, paramType='form'),
            dict(name='beer', type='int', description='Beer ID', required=True, paramType='form'),
        ],
    )
    @login_required
    def delete(self, id):
        from serveza.db import Bar, BarBeer, Beer

        bar = Bar.query.get_or_404(id)

        parser = reqparse.RequestParser()
        parser.add_argument('beer', type=int, required=True)
        args = parser.parse_args()

        beer = Beer.query.get_or_404(args.beer)

        BarBeer.query.filter(BarBeer.bar == bar, BarBeer.beer == beer).delete()
        db.session.commit()

        return 'ok'


class BarEvents(Resource):

    @swagger.operation()
    def get(self, id):
        from serveza.db import Bar

        bar = Bar.query.get_or_404(id)
        return jsonify(events=[event.as_json() for event in bar.events])

    @swagger.operation(
        parameters=[
            dict(api_token_param, paramType='form'),
            dict(name='name', type='string', description='Event name', required=True, paramType='form'),
            dict(name='start', type='string', description='Event start', paramType='form'),
            dict(name='end', type='string', description='Event start', paramType='form'),
            dict(name='description', type='string', description='Event description', paramType='form'),
            dict(name='location', type='string', description='Event location', paramType='form'),
        ],
    )
    @login_required
    def post(self, id):
        from serveza.db import Bar, BarEvent

        bar = Bar.query.get_or_404(id)

        def location(s):
            parts = s.split(',')
            parts = [part.strip() for part in parts]
            parts = [float(part) for part in parts]
            return tuple(parts)

        def date(s):
            print(s)
            return arrow.get(s)

        parser = reqparse.RequestParser()
        parser.add_argument('name', required=True)
        parser.add_argument('start', type=date)
        parser.add_argument('end', type=date)
        parser.add_argument('description')
        parser.add_argument('location', type=location)
        args = parser.parse_args()

        event = BarEvent(bar=bar, name=args.name)
        event.start = args.start
        event.end = args.end
        event.description = args.description
        event.location = args.location

        db.session.add(event)
        db.session.commit()

        return jsonify(event=event.as_json())

api.add_resource(Bars, '/bars')
api.add_resource(Bar, '/bars/<int:id>', endpoint='bar_details')
api.add_resource(
    BarComments, '/bars/<int:id>/comments', endpoint='bar_comments')
api.add_resource(BarBeers, '/bars/<int:id>/beers', endpoint='bar_beers')
api.add_resource(BarEvents, '/bars/<int:id>/events', endpoint='bar_events')
