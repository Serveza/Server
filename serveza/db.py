import arrow
import math
import struct
import sqlalchemy.types as types
from flask.ext.login import UserMixin
from flask.ext.sqlalchemy import SQLAlchemy
from functools import partial
from money import Money
from sqlalchemy import func
from sqlalchemy.engine import Engine
from sqlalchemy.event import listens_for
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy_utils import ArrowType, PasswordType, ScalarListType, URLType
from .settings import PASSWORD_SCHEMES

db = SQLAlchemy()

# Util functions


def generate_api_token():
    import uuid

    return uuid.uuid4().hex

# Custom types


class StructType(types.TypeDecorator):

    impl = types.Binary

    def __init__(self, fmt, *args, **kwargs):
        super().__init__(struct.calcsize(fmt), *args, **kwargs)
        self.fmt = fmt

    def process_bind_param(self, value, dialect):
        return struct.pack(self.fmt, *value)

    def process_result_value(self, value, dialect):
        return struct.unpack(self.fmt, value)


class MoneyType(types.TypeDecorator):

    impl = ScalarListType

    def process_bind_param(self, value, dialect):
        return [value.amount, value.currency]

    def process_result_value(self, value, dialect):
        [amount, currency] = value
        return Money(amount, currency)


PasswordType = partial(PasswordType, schemes=PASSWORD_SCHEMES)
LocationType = ScalarListType(float)

# Models


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(255), index=True, unique=True)
    password = db.Column(PasswordType())

    api_token = db.Column(db.String(32), default=generate_api_token)

    avatar = db.Column(URLType, nullable=True)
    firstname = db.Column(db.String, nullable=True)
    lastname = db.Column(db.String, nullable=True)

    last_event_check = db.Column(ArrowType)

    owner_bars = db.relationship('Bar', secondary='bar_owners')
    favorited_beers = db.relationship('Beer', secondary='user_beers')
    favorited_bars = db.relationship('Bar', secondary='user_bars')

    @property
    def fullname(self):
        return '%s %s' % (self.firstname, self.lastname)

    @classmethod
    def get_by_api_token(cls, api_token):
        return cls.query.get(cls.api_token == api_token)


class Bar(db.Model):
    __tablename__ = 'bars'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.Unicode)

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    image = db.Column(URLType)
    website = db.Column(URLType)

    owner = db.relationship('User', secondary='bar_owners', uselist=False)
    fans = db.relationship('User', secondary='user_bars')

    # Location properties / methods
    @property
    def position(self):
        return (self.latitude, self.longitude)

    @position.setter
    def position(self, value):
        (latitude, longitude) = value
        self.latitude = latitude
        self.longitude = longitude

    @property
    def address(self):
        from .settings import GEOLOCATOR

        location = GEOLOCATOR.reverse(self.position)
        return location.address

    @hybrid_method
    def distance(self, pos):
        # approximate radius of earth in km
        R = 6373.0

        (pos_lat, pos_lng) = pos
        pos_lat = math.radians(pos_lat)
        pos_lng = math.radians(pos_lng)

        rad_latitude = math.radians(self.latitude)
        rad_longitude = math.radians(self.longitude)

        delta_lat = pos_lat - rad_latitude
        delta_lng = pos_lng - rad_longitude

        a = math.sin(delta_lat / 2)**2 + math.cos(pos_lat) * \
            math.cos(rad_latitude) * math.sin(delta_lng / 2)**2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    @distance.expression
    def distance(cls, pos):
        # approximate radius of earth in km
        R = 6373.0

        (pos_lat, pos_lng) = pos
        pos_lat = math.radians(pos_lat)
        pos_lng = math.radians(pos_lng)

        rad_latitude = func.radians(cls.latitude)
        rad_longitude = func.radians(cls.longitude)

        delta_lat = pos_lat - rad_latitude
        delta_lng = pos_lng - rad_longitude

        a = func.pow(func.sin(delta_lat / 2), 2) + func.cos(pos_lat) * \
            func.cos(rad_latitude) * func.pow(func.sin(delta_lng / 2), 2)
        c = 2 * func.asin(func.sqrt(a))

        return R * c


class Beer(db.Model):
    __tablename__ = 'beers'

    id = db.Column(db.Integer, primary_key=True)

    image = db.Column(URLType)
    name = db.Column(db.Unicode)
    brewery = db.Column(db.Unicode)
    degree = db.Column(db.Float)
    description = db.Column(db.Text)

    fans = db.relationship('User', secondary='user_beers')


class BarBeer(db.Model):
    __tablename__ = 'bar_beers'

    bar_id = db.Column(db.Integer, db.ForeignKey('bars.id'), primary_key=True)
    beer_id = db.Column(
        db.Integer, db.ForeignKey('beers.id'), primary_key=True)

    price = db.Column(MoneyType)

    bar = db.relationship('Bar', backref='carte')
    beer = db.relationship('Beer', backref='bars')


class BarOwner(db.Model):
    __tablename__ = 'bar_owners'

    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), primary_key=True)
    bar_id = db.Column(db.Integer, db.ForeignKey('bars.id'), primary_key=True)


class UserBeer(db.Model):
    __tablename__ = 'user_beers'

    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), primary_key=True)
    beer_id = db.Column(
        db.Integer, db.ForeignKey('beers.id'), primary_key=True)


class UserBar(db.Model):
    __tablename__ = 'user_bars'

    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), primary_key=True)
    bar_id = db.Column(
        db.Integer, db.ForeignKey('bars.id'), primary_key=True)


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String)

    created_at = db.Column(ArrowType, default=arrow.get)

    __mapper_args__ = {
        'polymorphic_identity': 'notification',
        'polymorphic_on': type,
        'with_polymorphic': '*',
    }

    def as_json(self):
        return {
            'type': self.type,
            'created_at': self.created_at.datetime if self.created_at else None,
        }


class BarEvent(Notification):
    __tablename__ = 'bar_events'

    id = db.Column(
        db.Integer, db.ForeignKey('notifications.id'), primary_key=True)

    bar_id = db.Column(db.Integer, db.ForeignKey('bars.id'))

    start = db.Column(ArrowType, nullable=True)
    end = db.Column(ArrowType, nullable=True)

    name = db.Column(db.String)
    description = db.Column(db.Text, nullable=True)

    location = db.Column(LocationType, nullable=True)

    bar = db.relationship('Bar', backref='events')

    __mapper_args__ = {
        'polymorphic_identity': 'bar_event',
    }

    def as_json(self):
        from flask import url_for

        data = super().as_json()

        data['bar'] = url_for('api.bar_details', id=self.bar_id)

        data['start'] = self.start.datetime if self.start else None
        data['end'] = self.end.datetime if self.end else None

        data['name'] = self.name
        data['description'] = self.description

        data['location'] = self.location

        # Easier accesses for specific informations
        data['bar_image'] = self.bar.image

        return data


# Events


@listens_for(Engine, 'connect')
def on_connect(conn, record):
    try:
        import sqlite3

        # Configure needed functions for SQLite
        if isinstance(conn, sqlite3.Connection):
            conn.create_function("cos", 1, math.cos)
            conn.create_function("sin", 1, math.sin)
            conn.create_function("asin", 1, math.asin)
            conn.create_function("sqrt", 1, math.sqrt)
            conn.create_function("radians", 1, math.radians)
            conn.create_function("pow", 2, math.pow)
    except:
        pass
