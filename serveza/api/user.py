from flask import abort, jsonify
from flask_restful import Api, Resource
from flask_restful import fields, marshal, reqparse
from serveza.db import db
from .base import api, swagger

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


class UserNotifications(Resource):

    @swagger.operation()
    def get(self):
        import arrow
        from serveza.db import Bar, User, Notification, BarEvent

        parser = reqparse.RequestParser()
        parser.add_argument('api_token', required=True)
        parser.add_argument('bar', type=int, action='append', default=[])
        parser.add_argument('type')
        parser.add_argument('update', type=bool, default=False)
        args = parser.parse_args()

        user = User.query.filter(User.api_token == args.api_token).one()

        notifications = Notification.query

        if user.last_event_check is not None:
            notifications = notifications.filter(
                Notification.created_at >= user.last_event_check)

        if args.type is not None:
            notifications = notifications.filter(
                Notification.type == args.type)

        if len(args.bar) > 0:
            notifications = notifications.filter(BarEvent.bar_id.in_(args.bar))

        items = notifications.all()

        if args.update:
            user.last_event_check = arrow.get()
            db.session.add(user)

        return jsonify(notifications=[item.as_json() for item in items])

api.add_resource(UserLogin, '/user/login', endpoint='user_login')
api.add_resource(UserRegister, '/user/register', endpoint='user_register')
api.add_resource(UserNotifications, '/user/notifications', endpoint='user_notifications')
