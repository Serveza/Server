from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from .app import app
from .db import db

manager = Manager(app)

# Flask-Migrate
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

# Reset DB command
@manager.command
def resetdb():
    '''
        Reset the database.
    '''
    from .scripts.resetdb import reset_db

    app.config['SQLALCHEMY_ECHO'] = True
    db.drop_all()
    db.create_all()
    reset_db()

# Import beer
@manager.command
def import_beer(beer_name):
    '''
        Import a beer in the database.
    '''
    from serveza.utils.scrap.beer import scrap_beer
    from serveza.db import db

    beer = scrap_beer(beer_name)
    db.session.add(beer)
    db.session.commit()
