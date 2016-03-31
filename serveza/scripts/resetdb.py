import csv
import getpass
from geopy.geocoders import GoogleV3
from serveza.app import app
from serveza.db import db
from serveza.settings import PROJECT_ROOT, DB_PATH

DATA_DIR = PROJECT_ROOT / 'data'

# Data


def reset_data():
    reset_bars()
    reset_beers()
    reset_cartes()
    reset_events()


def data_reader(f):
    return csv.DictReader(f, delimiter=';')

# > Bars


def reset_bars():
    from serveza.db import Bar

    geolocator = GoogleV3()

    bars_file = DATA_DIR / 'bars.csv'
    with bars_file.open() as f:
        reader = data_reader(f)

        for row in reader:
            name = row['name']
            address = row['address']

            location = geolocator.geocode(address)

            bar = Bar(
                name=name, latitude=location.latitude, longitude=location.longitude)
            db.session.add(bar)

# > Beers


def reset_beers():
    import wikipedia
    from serveza.db import Beer

    def find_proper_image(urls):
        import re

        EXCLUDES = [
            'Emoji',
            'Disambig',
            'Hainaut',
            'Liste',
        ]
        PATTERNS = [
            r'\.svg$',
        ]

        for url in urls:
            good = True

            for word in EXCLUDES:
                if word in url:
                    good = False
                    break

            for pattern in PATTERNS:
                if re.search(pattern, url):
                    good = False
                    break

            if good:
                return url

        return None

    beers_file = DATA_DIR / 'beers.csv'
    with beers_file.open() as f:
        reader = data_reader(f)

        for row in reader:
            name = row['name']
            page = wikipedia.page(name, auto_suggest=True)

            beer = Beer(name=page.title)
            beer.image = find_proper_image(page.images)
            beer.brewery = row['brewery']
            beer.degree = row['degree']
            db.session.add(beer)

# > Cartes

def reset_cartes():
    from money import Money
    from serveza.db import Bar, Beer, BarBeer

    cartes_files = DATA_DIR / 'cartes.csv'
    with cartes_files.open() as f:
        reader = data_reader(f)

        for row in reader:
            try:
                bar = Bar.query.filter(Bar.name == row['barname']).one()
                beer = Beer.query.filter(Beer.name == row['beername']).one()

                (amount, currency) = row['price'].split()
                price = Money(amount, currency)

                entry = BarBeer(bar=bar, beer=beer, price=price)
                db.session.add(entry)
            except Exception as e:
                print(e)
                pass

# > Events

def reset_events():
    from serveza.db import Bar, BarEvent

    events_file = DATA_DIR / 'events.csv'
    with events_file.open() as f:
        reader = data_reader(f)

        for row in reader:
            try:
                bar = Bar.query.filter(Bar.name == row['barname']).one()

                name = row['name']

                event = BarEvent(bar=bar, name=name)
                db.session.add(event)
            except:
                pass

# Users


def reset_users():
    from serveza.db import User

    # Create super-user
    # admin_email = input('Superuser email: ')
    # admin_password = getpass.getpass('Superuser password: ')

    admin_email = 'kokakiwi+serveza@kokakiwi.net'
    admin_password = 'kiwi3291'
    admin_token = 'e2a52f2f73924017beb8fab0e8529182'

    admin = User(
        email=admin_email, password=admin_password, api_token=admin_token)
    db.session.add(admin)

    toto = User(email='toto', password='titi', firstname='Pinkie', lastname='Pie', avatar='http://i.imgur.com/hapjgQi.png')
    db.session.add(toto)

    aang = User(email='aang', password='zuko', firstname='Aang', avatar='http://i.imgur.com/5h2fDdT.jpg')
    db.session.add(aang)

    print('Superuser token:', admin.api_token)


def reset_db():
    # Reset all data
    reset_data()
    reset_users()

    db.session.commit()


def main():
    app.config['SQLALCHEMY_ECHO'] = True
    app.test_request_context().push()

    reset_db()
