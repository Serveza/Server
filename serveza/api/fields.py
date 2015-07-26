from flask import url_for
from flask_restful import fields

BAR_BEER_FIELDS = {
    'id': fields.Integer(attribute=lambda entry: entry.beer_id),
    'url': fields.String(attribute=lambda entry: url_for('.beer_details', id=entry.beer.id)),
    'name': fields.String(attribute=lambda entry: entry.beer.name),
    'price': fields.String,
}

BAR_COMMENT_AUTHOR_FIELDS = {
    'avatar': fields.String,
    'firstname': fields.String,
}

BAR_COMMENT_FIELDS = {
    'score': fields.Integer,
    'comment': fields.String,
    'author': fields.Nested(BAR_COMMENT_AUTHOR_FIELDS),
}

BEER_COMMENT_AUTHOR_FIELDS = {
    'avatar': fields.String,
    'firstname': fields.String,
}

BEER_COMMENT_FIELDS = {
    'score': fields.Integer,
    'comment': fields.String,
    'author': fields.Nested(BAR_COMMENT_AUTHOR_FIELDS),
}

BAR_DETAILS_FIELDS = {
    'id': fields.Integer,
    'name': fields.String,
    'position': fields.FormattedString('{latitude}, {longitude}'),
    'address': fields.String,
    'carte': fields.List(fields.Nested(BAR_BEER_FIELDS)),
    'image': fields.String,
    'website': fields.String,
}

BAR_LIST_FIELDS = {
    'id': fields.Integer,
    'url': fields.Url('.bar_details'),
    'name': fields.String,
    'position': fields.FormattedString('{latitude}, {longitude}'),
}

BEER_LIST_FIELDS = {
    'id': fields.Integer,
    'url': fields.Url('.beer_details'),
    'name': fields.String,
}

BEER_DETAILS_FIELDS = {
    'id': fields.Integer,
    'url': fields.Url('.beer_details'),
    'name': fields.String,
    'image': fields.String,
    'description': fields.String,
    'brewery': fields.String,
    'degree': fields.Float,
}

USER_DETAILS_FIELDS = {
    'email': fields.String(),
    'firstname': fields.String(),
    'lastname': fields.String(),
    'api_token': fields.String(),
    'avatar': fields.String(),
}
