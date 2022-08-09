"""
This is the main script
"""

import requests
import json
from bs4 import BeautifulSoup


class SearchPage(object):
    def __init__(self, url: str = 'https://ufa.flamp.ru/search/%D0%B2%D0%BA%D1%83%D1%81%D0%BD%D0%BE%20%D0%B8%20%D1%82%D0%BE%D1%87%D0%BA%D0%B0'):
        self.url = url
        self.urls = []

    def get_search_urls(self):
        url = self.url
        url_head = 'https:'
        while True:
            rs = requests.get(url)
            rs.raise_for_status()
            root = BeautifulSoup(rs.content.decode('utf-8', 'ignore'), 'html.parser')
            body = root.find_all("data-marker")
            for data in body:
                self.urls.append(url_head + data['url'])
            try:
                next_button = data.find("li", attrs={"class": "pagination__item pagination__item--next"})
                url = url_head + next_button.find('a').get("href")
            except AttributeError:
                print('Search END')
                break
        return self.urls


class ReviewsManager(object):
    def __init__(self, urls: list[str]):
        self.urls = urls
        self.reviews = []

    def get_root(self, url):
        rs = requests.get(url)
        rs.raise_for_status()
        soup = BeautifulSoup(rs.content.decode('utf-8', 'ignore'), 'html.parser')
        return soup

    def get_reviews(self):
        for url in self.urls:
            root = self.get_root(url)
            body = root.find_all("article", attrs={"itemtype": "http://schema.org/Review"})
            for article in body:
                review = {}
                article.find_all("meta")
                # print(article.find_all("meta"))
                review['url'] = 'https:' + article.find("cat-brand-ugc-date").get("url")
                review['author'] = article.find("meta", attrs={'itemprop': "name"}).get("content")
                review['datetime'] = article.find("meta", attrs={'itemprop': "datePublished"}).get("content")
                review['rate'] = article.find("meta", attrs={'itemprop': "ratingValue"}).get("content")

                # FIXME
                text = article.find_all("p")
                # review['text'] = [par.text.strip() for par in text]
                review_text = ""
                for par in text:
                    review_text += par.text.strip()
                review['text'] = review_text


                # print(review)
                self.reviews.append(review)
                # break
            # break
        return self.reviews


# class SearchPage2gis(object):
#     def __init__(self,
#                  url: str = 'https://2gis.ru/ufa/search/%D0%B2%D0%BA%D1%83%D1%81%D0%BD%D0%BE%20%D0%B8%20%D1%82%D0%BE%D1%87%D0%BA%D0%B0'):
#         self.url = url
#         self.urls = []
#
#     def get_root(self, url):
#         rs = requests.get(url)
#         rs.raise_for_status()
#         soup = BeautifulSoup(rs.content.decode('utf-8', 'ignore'), 'html.parser')
#         return soup
#
#     def get_search_urls(self):
#         url = self.url
#         while True:
#             root = self.get_root(url)
#             body = root.find_all("data-marker")
#             for data in body:
#                 self.urls.append('https:' + data['url'])
#             try:
#                 next_button = data.find("li", attrs={"class": "pagination__item pagination__item--next"})
#                 url = 'https:' + next_button.find('a').get("href")
#             except AttributeError:
#                 print('Search END')
#                 break
#         return self.urls



search = SearchPage(
    'https://ufa.flamp.ru/search/%D0%B2%D0%BA%D1%83%D1%81%D0%BD%D0%BE%20%D0%B8%20%D1%82%D0%BE%D1%87%D0%BA%D0%B0')
vit_urls = search.get_search_urls()

reviews = ReviewsManager(vit_urls)
reviews_struct = reviews.get_reviews()
print(reviews_struct)

with open('reviews.json', 'w') as fout:
    json.dump(reviews_struct, fout)

with open('reviews.json', 'r') as fin:
    output = json.load(fin)
    print(output)



