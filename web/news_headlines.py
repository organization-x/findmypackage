import json

from datetime import datetime, timedelta, timezone

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup

from .models import NewsHeadline
from .gpt3 import rate_news_headlines, retrieve_countries_from_headlines


class AssociatedPress:
    def __init__(self):
        self.url = 'https://apnews.com/hub/world-news'

    def get_world_headlines(self):
        headlines = []
        world_news_response = requests.get(self.url)
        content = world_news_response.content

        data = BeautifulSoup(content, 'lxml')
        headline_cards = data.find_all('div', class_='CardHeadline')
        for headline_card in headline_cards:
            headlines.append({
                'headline': headline_card.find('h2').text,
                'date': headline_card.find('span', class_='Timestamp').get('data-source')
            })
        return headlines

# for natural disasters
class ReliefWeb:
    def __init__(self):
        current_date = datetime.now(timezone.utc)
        self.url = (
            'https://api.reliefweb.int/v1/disasters?appname=FindMyPackage'
            '&filter[field]=date.created'
            f'&filter[value][from]={self.format_date(current_date - timedelta(days=14))}'
            f'&filter[value][to]={self.format_date(current_date)}'
            '&profile=full'
        )

    def format_date(self, date):
        return f"{date.strftime('%Y-%m-%dT%H:%M:%S')}%2B00:00"

    def get_recent_disasters(self):
        recent_disasters = []
        disasters = json.loads(requests.get(self.url).content).get('data')
        if disasters is None:
            return recent_disasters
        for disaster in disasters:
            if (fields := disaster.get('fields')) is None:
                continue
            recent_disasters.append({
                'name': fields.get('name'),
                'date': fields.get('date', {}).get('changed'),
                'countries_affected': [country.get('name') for country in fields.get('country')],
            })
        return recent_disasters


def update_database_headlines():
    # update with new headlines from associated press
    for headline in AssociatedPress().get_world_headlines():
        if not NewsHeadline.objects.filter(headline=headline.get('headline')).exists():
            NewsHeadline.objects.create(headline=headline.get('headline'), date=headline.get('date'))

    # update with new disasters from reliefweb
    for disaster in ReliefWeb().get_recent_disasters():
        if not NewsHeadline.objects.filter(headline=disaster.get('name')).exists():
            NewsHeadline.objects.create(
                countries_affected=json.dumps({'countries': disaster.get('countries_affected')}),
                headline=disaster.get('name'), date=disaster.get('date'), impact_score=100)

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
            "countries": next(countries, ["Nowhere"])
        })
        news_headline.save()

def start_job():
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_database_headlines, 'interval', minutes=30)
    scheduler.start()
