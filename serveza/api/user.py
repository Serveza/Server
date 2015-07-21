from flask import abort, jsonify
from flask_restful import fields, marshal, reqparse
from .base import api_blueprint

USER_FIELDS = {
    'email': fields.String(),
    'firstname': fields.String(),
    'lastname': fields.String(),
    'api_token': fields.String(),
    'avatar': fields.String(),
}

@api_blueprint.route('/user/login', methods=['GET', 'POST'])
def login():
    from serveza.db import User

    parser = reqparse.RequestParser()
    parser.add_argument('email', required=True)
    parser.add_argument('password', required=True)
    args = parser.parse_args()

    user = User.query.filter(User.email == args.email).first()

    if user is None or user.password != args.password:
        abort(403)

    return jsonify(**marshal(user, USER_FIELDS))


@api_blueprint.route('/user/register', methods=['POST'])
def register():
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

    return jsonify(**marshal(user, USER_FIELDS))
