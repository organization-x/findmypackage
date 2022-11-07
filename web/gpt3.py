import json
from datetime import timedelta

import openai
from dateutil import parser
import requests

from package.settings import SECRETS

from .models import NewsHeadline

openai.api_key = SECRETS['OPENAI_SECRET']


class GPT_Completion():
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
        'EXAMPLES:\n1. Ship ports are closed down: 70\n2. Natural disaster arrives at a country: 100\n3. Less than five-hundred people die because of a tragic event: 0\n4. Pandemic spreads to a large country: 80\n\nNEWS HEADLINES:'
    )
    for i, event in enumerate(news_headlines):
        prompt += f'\n{i+1}. {event}'
    response = GPT_Completion(prompt).get_response()

    current_number = 1
    headline_ratings = []
    for line in response.splitlines():
        if line.startswith(f'{current_number}. '):
            headline_rating = line.split()[-1]
            headline_ratings.append(int(headline_rating) if headline_rating.isnumeric() else -1)
            current_number += 1
    return headline_ratings


def retrieve_countries_from_headlines(news_headlines):
    prompt = 'Retrieve the country names affected for each event from each news headline, numbered below:\n\nNEWS HEADLINES:\n'
    for i, event in enumerate(news_headlines):
        prompt += f'\n{i+1}. {event}'
    response = GPT_Completion(prompt).get_response()

    current_number = 1
    total_countries = []
    for line in response.splitlines():
        if line.startswith(f'{current_number}. '):
            current_countries = line.removeprefix(f'{current_number}. ').split(',')
            total_countries.append([country.replace('and ', '').strip() for country in current_countries])
            current_number += 1
    return total_countries


def calculate_delivery_delay(eta: str, package_location):
    response = {'days': '', 'hours': '', 'headlines': []}
    if not eta or eta.lower() == 'n/a':
        return response

    # convert string to datetime
    eta = parser.parse(eta)
    adjusted_eta = eta
    affected_headlines = []

    package_address = f"{package_location.get('city')} {package_location.get('state')}, {package_location.get('country')}"

    news_headlines = NewsHeadline.objects.filter(impact_score__gte=10)
    for news_headline in news_headlines:
        impact_score = news_headline.impact_score

        countries = json.loads(news_headline.countries_affected).get('countries')
        for country in countries:
            if country.lower() in ('nowhere', 'n/a', '-', 'none') or not country:
                continue
            distance_relevance = calculate_distance_relevance(package_address, country)
            if distance_relevance > 0:
                impact_score *= distance_relevance
                affected_headlines.append(news_headline.headline)
                break

        # check if impact score increased from the countries
        if impact_score > news_headline.impact_score:
            adjusted_eta += timedelta(hours=impact_score / 3)

    delay = adjusted_eta - eta
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
    print(data)
    relevance_function = all_other_relevance_function
    destination_address, origin_address = data.get('destination_addresses', [''])[0].lower(), data.get('origin_addresses', [''])[0].lower()
    if ('usa' in destination_address or 'united states' in destination_address) and ('usa' in origin_address or 'united states' in origin_address):
        relevance_function = united_states_relevance_function
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


# ---------------------------------------------------------------------------- #
#                                    Testing                                   #
# ---------------------------------------------------------------------------- #

news_headlines = ['Iran also barred from Nobel ceremony, after Russia, Belaru', 'Ship ports closed everywhere',
                  'Celebrity wins an oscar award', 'Famous person has died', 'Minor pandemic spreads to America']
real_events = ["Tropical Depression Lisa crosses into southern Mexico", "Russia is suspending a Ukraine grain export deal that has helped keep food prices down", "World Series rainout, Astros-Phils to play Game 3 Tuesday", 'The Coronavirus Impact on Personal Finances']

# print(rate_news_headlines(real_events))
# print(retrieve_countries_from_headlines(other))

# for adjusted eta testing, uncomment and runserver to test
# print('Start time:', datetime.now().strftime("%H:%M:%S"))
# print('End time:  ', calculate_delivery_delay(
#     datetime.now(), 
#     {
#         'streetLines': [
#             'Not available'
#         ],
#         'city': 'Los Angeles',
#         'state': 'California',
#         'postalCode': '90001',
#         'country': 'United States'
#     }
# ))
print(calculate_distance_relevance('Cerritos California', 'Florida USA'))
print(calculate_distance_relevance('Houston Texas', 'USA'))
