import json

from datetime import datetime, timedelta, timezone

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup

from .models import NewsHeadline
from .gpt3 import rate_news_headlines, retrieve_countries_from_headlines


class AssociatedPress:
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
    # update with new headlines from associated press
    for headline in AssociatedPress().get_world_headlines():
        if not NewsHeadline.objects.filter(headline=headline.get('headline')).exists():
            NewsHeadline.objects.create(headline=headline.get('headline'), date=headline.get('date'))

    # set fields of headlines that have not yet been set
    headlines_for_generation = []
    for headline in NewsHeadline.objects.filter(impact_score=-1):
        headlines_for_generation.append(headline)
        if len(headlines_for_generation) > 5:
            generate_fields_for_headlines(headlines_for_generation)
            headlines_for_generation = []
    generate_fields_for_headlines(headlines_for_generation)

    # delete news headlines older than 14 days
    NewsHeadline.objects.filter(date__lte=datetime.now(timezone.utc) - timedelta(days=14)).delete()

def generate_fields_for_headlines(news_headlines):
    if len(news_headlines) < 1:
        return
    headline_texts = [news_headline.headline for news_headline in news_headlines]
    ratings = iter(rate_news_headlines(headline_texts))
    countries = iter(retrieve_countries_from_headlines(headline_texts))
    for news_headline in news_headlines:
        news_headline.impact_score = next(ratings, -1)
        news_headline.countries_affected = json.dumps({
            'countries': next(countries, ['Nowhere'])
        })
        news_headline.save()

def start_job():
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_database_headlines, 'interval', minutes=30)
    scheduler.start()
    