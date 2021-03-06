import wikipedia
from ratebeer import RateBeer

wikipedia.set_lang('fr')

def scrap_beer(name):
    from serveza.db import Beer

    try:
        page = wikipedia.page(name, auto_suggest=True)
        rb = RateBeer()
        rb_beer = rb.search(page.title)['beers'][0]
    except Exception as e:
        return None

    rb_beer._populate()

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

    beer = Beer(name=page.title)
    beer.image = find_proper_image(page.images)
    beer.description = rb_beer.description
    beer.brewery = rb_beer.brewery
    beer.degree = rb_beer.abv

    return beer
