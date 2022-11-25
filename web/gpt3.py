import json
from datetime import timedelta, datetime
import openai
import requests
from package.settings import SECRETS
from .models import NewsHeadline

openai.api_key = SECRETS['OPENAI_SECRET']


class GptCompletion():
    def __init__(self, prompt):
        self.prompt = prompt

    def get_response(self):
        response = openai.Completion.create(
            model='text-davinci-002',
            prompt=self.prompt,
            temperature=0,
            max_tokens=340,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )
        return response.choices[0].text


def rate_news_headlines(news_headlines):
    prompt = (
        'Decide a score out of 0 to 100 for each event from each news headline, numbered below, based on how much the event would delay world-wide transportation today:\n\n'
        'EXAMPLES:\n1. Ship ports are closed down: 70\n2. Natural disaster arrives at a country: 100\n3. Less than five-hundred people die because of a tragic event: 0\n4. Pandemic spreads to a large country: 80\n5. A country practices to attack another country: 0\n\nNEWS HEADLINES:'
    )
    for i, event in enumerate(news_headlines):
        prompt += f'\n{i+1}. {event}'
    response = GptCompletion(prompt).get_response()

    current_number = 1
    headline_ratings = []
    for line in response.splitlines():
        if line.startswith(f'{current_number}. '):
            headline_rating = line.split()[-1]
            headline_ratings.append(int(headline_rating) if headline_rating.isnumeric() else -1)
            current_number += 1
    return headline_ratings


def retrieve_countries_from_headlines(news_headlines):
    prompt = 'Retrieve the country name, with the state or city name if possible, affected for each event from each news headline, numbered below:\n\nNEWS HEADLINES:\n'
    for i, event in enumerate(news_headlines):
        prompt += f'\n{i+1}. {event}'
    response = GptCompletion(prompt).get_response()

    current_number = 1
    total_countries = []
    for line in response.splitlines():
        if line.startswith(f'{current_number}. '):
            current_countries = line.removeprefix(f'{current_number}. ').split(',')
            total_countries.append([country.replace('and ', '').strip() for country in current_countries])
            current_number += 1
    return total_countries


def calculate_delivery_delay(status: str, package_location):
    response = {'days': '', 'hours': '', 'headlines': []}
    if 'delivered' in status.lower() or status.lower() == 'n/a' or not status:
        return response

    # convert string to datetime
    start_time = datetime.now()
    adjusted_eta = datetime.now()
    affected_headlines = []

    package_address = f"{package_location.get('city')} {package_location.get('state')}, {package_location.get('country')}"

    news_headlines = NewsHeadline.objects.filter(impact_score__gte=10)
    for news_headline in news_headlines:
        countries = json.loads(news_headline.countries_affected).get('countries')
        for country in countries:
            if country.lower() in ('nowhere', 'n/a', '-', 'none') or not country:
                continue
            distance_relevance = calculate_distance_relevance(package_address, country)
            if distance_relevance > 0:
                total_impact_score = news_headline.impact_score * (distance_relevance / 100)
                affected_headlines.append(news_headline.headline)
                adjusted_eta += timedelta(hours=total_impact_score)
                break

    delay = adjusted_eta - start_time
    response['days'] = delay.days
    response['hours'] = delay.seconds / 3600
    response['headlines'] = affected_headlines[:3] # cap off displaying affected headlines to 3
    return response


# returns a number 1 to 100 based on how close the two locations are ( closer to 100 means the locations are closer )
def calculate_distance_relevance(origin, destination):
    url = 'https://maps.googleapis.com/maps/api/distancematrix/json'
    params = {
        'origins': origin,
        'destinations': destination,
        'units': 'imperial',
        'key': SECRETS['FMP_MAPS_KEY']
    }
    response = requests.get(url, params=params)
    data = json.loads(response.content)
    relevance_function = all_other_relevance_function
    destination_address, origin_address = f" {data.get('destination_addresses', [''])[0].lower()} ", f" {data.get('origin_addresses', [''])[0].lower()} "
    if (' usa' in destination_address or ' united states ' in destination_address or ' us ' in destination_address) and (' usa ' in origin_address or ' united states' in origin_address or ' us ' in origin_address):
        relevance_function = united_states_relevance_function
    elif (destination_address in origin_address) or (origin_address in destination_address):
        return 100
    if not data.get('destination_addresses', [''])[0] or not data.get('origin_addresses', [''])[0]:
        return 0
    data = data.get('rows')[0].get('elements', [{}])[0]
    if data.get('status') == 'ZERO_RESULTS':
        return 0
    distance = data.get('distance', {}).get('text')
    distance = distance[:distance.rfind(' ')].replace(',', '')
    relevance = relevance_function(int(distance))
    if relevance < 0.5:
        relevance = 0
    return relevance


def united_states_relevance_function(distance):
    return -0.00001 * (distance ** 2) + 100

def all_other_relevance_function(distance):
    return 2 ** (6.644 - (0.007 * distance))
