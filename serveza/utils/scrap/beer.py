import wikipedia
from ratebeer import RateBeer

rb = RateBeer()

wikipedia.set_lang('fr')

def scrap_beer(name):
    from serveza.db import Beer

    page = wikipedia.page(name)
    rb_result = rb.search(name)['beers'][0]
    rb_beer = rb.get_beer(rb_result['url'])

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
