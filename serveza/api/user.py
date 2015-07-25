from contextlib import suppress
from flask import abort, jsonify
from flask_restful import Api, Resource
from flask_restful import fields, marshal, reqparse
from serveza.db import db
from serveza.login import current_user, login_required
from .base import api, swagger

# User login / register
@swagger.model
class UserModel:

    resource_fields = {
        'email': fields.String(),
        'firstname': fields.String(),
        'lastname': fields.String(),
        'api_token': fields.String(),
        'avatar': fields.String(),
    }


class UserLogin(Resource):

    @swagger.operation()
    def post(self):
        from serveza.db import User

        parser = reqparse.RequestParser()
        parser.add_argument('email', required=True)
        parser.add_argument('password', required=True)
        args = parser.parse_args()

        user = User.query.filter(User.email == args.email).first()

        if user is None or user.password != args.password:
            abort(403)

        return jsonify(**marshal(user, UserModel.resource_fields))

    @swagger.operation()
    def get(self):
        return self.post()


class UserRegister(Resource):

    @swagger.operation()
    def post(self):
        from serveza.db import db
        from serveza.db import User

        parser = reqparse.RequestParser()
        parser.add_argument('email', required=True)
        parser.add_argument('password', required=True)
        parser.add_argument('firstname')
        parser.add_argument('lastname')
        parser.add_argument('avatar')
        args = parser.parse_args()

        if User.query.filter(User.email == args.email).first() is not None:
            abort(409)

        user = User(email=args.email, password=args.password)
        user.firstname = args.firstname
        user.lastname = args.lastname
        user.avatar = args.avatar

        db.session.add(user)
        db.session.commit()

        return jsonify(**marshal(user, UserModel.resource_fields))

api.add_resource(UserLogin, '/user/login', endpoint='user_login')
api.add_resource(UserRegister, '/user/register', endpoint='user_register')

# User notifications
class UserNotifications(Resource):

    @swagger.operation()
    @login_required
    def get(self):
        import arrow
        from serveza.db import Bar, User, Notification, BarEvent

        parser = reqparse.RequestParser()
        parser.add_argument('bar', type=int, action='append', default=[])
        parser.add_argument('type')
        parser.add_argument('update', type=bool, default=False)
        args = parser.parse_args()

        notifications = Notification.query

        if current_user.last_event_check is not None:
            notifications = notifications.filter(
                Notification.created_at >= current_user.last_event_check)

        if args.type is not None:
            notifications = notifications.filter(
                Notification.type == args.type)

        if len(args.bar) > 0:
            notifications = notifications.filter(BarEvent.bar_id.in_(args.bar))

        items = notifications.all()

        if args.update:
            current_user.last_event_check = arrow.get()

        return jsonify(notifications=[item.as_json() for item in items])

api.add_resource(UserNotifications, '/user/notifications', endpoint='user_notifications')

# User favorites
class UserFavoriteBeers(Resource):

    @swagger.operation()
    @login_required
    def get(self):
        from .beers import BEER_LIST_FIELDS

        beers = current_user.favorited_beers
        return marshal(beers, BEER_LIST_FIELDS)

    @swagger.operation()
    @login_required
    def post(self):
        from serveza.db import Beer

        parser = reqparse.RequestParser()
        parser.add_argument('beer', type=int)
        args = parser.parse_args()

        beer = Beer.query.get(args.beer)

        if beer is not None:
            current_user.favorited_beers.append(beer)

        return 'ok'

    @swagger.operation()
    @login_required
    def delete(self):
        from serveza.db import Beer

        parser = reqparse.RequestParser()
        parser.add_argument('beer', type=int)
        args = parser.parse_args()

        beer = Beer.query.get(args.beer)
        if beer is not None:
            with suppress(ValueError):
                current_user.favorited_beers.remove(beer)

        return 'ok'

class UserFavoriteBars(Resource):

    @swagger.operation()
    @login_required
    def get(self):
        from .bars import BAR_LIST_FIELDS

        bars = current_user.favorited_bars
        return marshal(bars, BEER_LIST_FIELDS)

    @swagger.operation()
    @login_required
    def post(self):
        from serveza.db import Bar

        parser = reqparse.RequestParser()
        parser.add_argument('bar', type=int)
        args = parser.parse_args()

        bar = Bar.query.get(args.bar)

        if bar is not None:
            current_user.favorited_bars.append(bar)

        return 'ok'

    @swagger.operation()
    @login_required
    def delete(self):
        from serveza.db import Bar

        parser = reqparse.RequestParser()
        parser.add_argument('bar', type=int)
        args = parser.parse_args()

        bar = Bar.query.get(args.bar)
        if bar is not None:
            with suppress(ValueError):
                current_user.favorited_bars.remove(bar)

        return 'ok'


api.add_resource(UserFavoriteBeers, '/user/favorites/beers')
api.add_resource(UserFavoriteBars, '/user/favorites/bars')
