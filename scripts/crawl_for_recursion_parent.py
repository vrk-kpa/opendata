import logging
from urllib.parse import urljoin
import requests
# You need to install bs4 with `pip install beautifulsoup4`
from bs4 import BeautifulSoup

logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.DEBUG)

class Crawler:

    def __init__(self, urls=[]):
        self.visited_urls = []
        self.urls_to_visit = urls
        self.organization_as_parent = []

    def download_url(self, url):
        return requests.get(url, headers={'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}).text

    def get_linked_urls(self, url, html):
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.select('.pagination > li > a'):
            path = link.get('href')
            if path and path.startswith('/'):
                path = urljoin(url, path)

            if path != '#':
                yield path

    def get_dummy_parent(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        for organization_list_item in soup.select('.organization-list > li'):
            parent = organization_list_item.select('.parent-organization')
            org = organization_list_item.select('.organization-title')
            if parent[0].name == 'a' and org[0].name == 'a':
                if parent[0].get('href') == org[0].get('href'):
                    self.organization_as_parent.append(org[0].get('href'))

    def add_url_to_visit(self, url):
        if url not in self.visited_urls and url not in self.urls_to_visit:
            self.urls_to_visit.append(url)

    def crawl(self, url):
        html = self.download_url(url)
        self.get_dummy_parent(html)
        for url in self.get_linked_urls(url, html):
            self.add_url_to_visit(url)

    def run(self):
        i = 0
        while True:
            try:
                url = self.urls_to_visit[i]
                logging.info(f'Crawling: {url}')
                try:
                    self.crawl(url)
                except Exception:
                    logging.exception(f'Failed to crawl: {url}')
                finally:
                    self.visited_urls.append(url)
            except IndexError:
                break
            i += 1
        logging.info(self.organization_as_parent)

if __name__ == '__main__':
    Crawler(urls=['https://www.avoindata.fi/data/fi/organization/?q=&only_with_datasets=False']).run()
