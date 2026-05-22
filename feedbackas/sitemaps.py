from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    """
    Svetainės žemėlapis viešiems statiniams puslapiams.
    Generuoja URL'us su prioritetais ir keitimosi dažnumu.
    """
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return [
            {'name': 'index', 'priority': 1.0},
            {'name': 'apie_mus', 'priority': 0.8},
            {'name': 'saugumas', 'priority': 0.8},
        ]

    def location(self, item):
        return reverse(item['name'])

    def priority(self, item):
        return item['priority']
