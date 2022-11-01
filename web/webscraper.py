from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

from .models import NewsHeadline


class WebScraper:
    def __init__(self):
        self.news_url = 'https://apnews.com/hub/world-news'

    def get_world_headlines(self):
        headlines = []
        world_news_response = requests.get(self.news_url)
        content = world_news_response.content

        data = BeautifulSoup(content, 'lxml')
        headline_cards = data.find_all('div', class_='CardHeadline')
        for headline_card in headline_cards:
            headlines.append({
                'headline': headline_card.find('h2').text,
                'date': headline_card.find('span', class_='Timestamp').get('data-source')
            })
        return headlines

def update_database_headlines():
    for headline in WebScraper().get_world_headlines():
        if NewsHeadline.objects.filter(headline=headline.get('headline')).exists(): continue
        NewsHeadline.objects.create(headline=headline.get('headline'), date=headline.get('date'))
    # delete news headlines older than 14 days
    NewsHeadline.objects.filter(date__lte=datetime.now(timezone.utc)-timedelta(days=14)).delete()
