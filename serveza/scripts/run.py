from argparse import ArgumentDefaultsHelpFormatter
from argparse import ArgumentParser
from serveza.app import app


def main(args):
    app.config['DEBUG'] = app.config['SQLALCHEMY_ECHO'] = args.debug

    app.run(host=args.host, port=args.port)

parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument(
    '-d', '--debug', action='store_true', help='Enable debug mode.')
parser.add_argument(
    '-H', '--host', default='127.0.0.1', help='Host to listen connections.')
parser.add_argument(
    '-P', '--port', default=5000, help='Port to listen connections.')


def entry():
    main(parser.parse_args())
