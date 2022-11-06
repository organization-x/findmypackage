import json
from datetime import datetime, timedelta

import openai

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
        'EXAMPLES:\n1. Ship ports are closed down: 70\n2. Natural disaster arrives at a country: 100\n3. Tragic event happens and less than a thousand people die: 0\n4. Pandemic spreads to a large country: 80\n\nNEWS HEADLINES:'
    )
    for i, event in enumerate(news_headlines):
        prompt += f'\n{i+1}. {event}'
    response = GPT_Completion(prompt).get_response()

    current_number = 1
    headline_ratings = []
    for headline_rating in response.splitlines():
        if headline_rating.startswith(f'{current_number}. '):
            headline_ratings.append(headline_rating.split()[-1])
            current_number += 1
    return headline_ratings


def retrieve_countries_from_headlines(news_headlines):
    prompt = 'Retrieve the countries affected for each event from each news headline, numbered below:\n\nNEWS HEADLINES:\n'
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


def get_adjusted_eta(eta: datetime):
    adjusted_eta = eta
    # get all news headlines with an impact score greater than or equal to 10
    news_headlines = NewsHeadline.objects.filter(impact_score__gte=10)
    for news_headline in news_headlines:
        # do something with countries here
        countries = json.loads(news_headline.countries_affected).get('countries')
        # do something with impact score here (from 0 of 100)
        impact_score = news_headline.impact_score
        # add to the adjusted eta
        adjusted_eta += timedelta(hours=news_headline.impact_score / 100)
    return adjusted_eta


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
# print('End time:  ', get_adjusted_eta(datetime.now()).strftime("%H:%M:%S"))