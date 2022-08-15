import requests
from bs4 import BeautifulSoup
import datetime


class SearchPage(object):
    """
    This class searches for all Vkusno i tochka urls in https://ufa.flamp.ru
    and outputs the list of urls
    """
    def __init__(self, url: str = 'https://ufa.flamp.ru/search/%D0%B2%D0%BA%D1%83%D1%81%D0%BD%D0%BE%20%D0%B8%20%D1%82'
                                  '%D0%BE%D1%87%D0%BA%D0%B0'):
        """
        This is the constructor of class SearchPage
        :param url: the rearch page
        """
        self.url = url
        self.urls = []

    def get_search_urls(self):
        """
        Is parsing the search page and collecting all url of vkusno i tochka
        :return: list of vkusno i tochka urls on ufa.flamp.ru
        """
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
                break
        return self.urls


def make_review(article) -> dict:
    """
    Makes the dict review from an article from the url page
    :param article: from the url
    :return: the dict review
    """
    review = {}
    article.find_all("meta")
    review['url'] = 'https:' + article.find("cat-brand-ugc-date").get("url")
    review['author'] = article.find("meta", attrs={'itemprop': "name"}).get("content")
    review['datetime'] = article.find("meta", attrs={'itemprop': "datePublished"}).get("content")
    review['rate'] = article.find("meta", attrs={'itemprop': "ratingValue"}).get("content")

    text = article.find_all("p")
    review_text = ""
    for par in text:
        review_text += par.text.strip()
    review['text'] = review_text
    return review


def get_root(url):
    """
    Gets the BeautifulSoup from the input url
    :param url: input url
    :return: BeautifulSoup of the url
    """
    rs = requests.get(url)
    rs.raise_for_status()
    soup = BeautifulSoup(rs.content.decode('utf-8', 'ignore'), 'html.parser')
    return soup


class ReviewsManager(object):
    """
    This class manages the reviews on each url
    """
    def __init__(self, urls: list[str]):
        """
        This is the constructor of ReviewsManager
        :param urls:
        """
        self.urls = urls
        self.reviews = []
        self.last_update_datetime = ''

    def get_new_reviews(self) -> list:
        """
        Gets the reviews from the urls the day ago from the now
        :return: the list of the new reviews
        """
        for url in self.urls:
            root = get_root(url)
            body = root.find_all("article", attrs={"itemtype": "http://schema.org/Review"})
            for article in body:
                article_datetime = article.find("meta", attrs={'itemprop': "datePublished"}).get("content")  # str MSK
                article_datetime = datetime.datetime.strptime(article_datetime, "%Y-%m-%dT%H:%M:%S+03:00")  # dt MSK
                article_datetime = article_datetime - datetime.timedelta(hours=3)  # UTC +0
                if (datetime.datetime.now() - article_datetime) < datetime.timedelta(days=40):
                    self.reviews.append(make_review(article))
                else:
                    break
        return self.reviews

    def get_reviews(self):
        """
        Get all reviews from the page
        :return: the list of the new reviews
        """
        for url in self.urls:
            root = get_root(url)
            body = root.find_all("article", attrs={"itemtype": "http://schema.org/Review"})
            for article in body:
                self.reviews.append(make_review(article))
        return self.reviews


def search_for_vit_pages() -> list:
    """
    Gets the vkusno i tochka urls from search page
    :return: list of urls
    """
    search = SearchPage()
    vit_urls = search.get_search_urls()
    return vit_urls


def get_new_vit_reviews(urls: list) -> list:
    """
    Gets the new reviews from the urls
    :param urls: list of urls
    :return: list of new reviews
    """
    reviews = ReviewsManager(urls)
    new_reviews = reviews.get_new_reviews()
    return new_reviews
