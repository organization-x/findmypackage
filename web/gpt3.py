import openai

from package.settings import SECRETS

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


def get_adjusted_eta(eta):
    # work on this
    pass


def rate_news_headlines(news_headlines):
    prompt = (
        'Decide a score out of 0 to 100 based on how much each event from each news headline, numbered below, would delay world-wide transportation today:\n\n'
        'EXAMPLES:\n1. Ship ports closed in America: 70\n2. Typhoon approaching China: 70\n3. Heavy snowfall in California: 80\n4. Pandemic spreads to Mexico: 80\n\nSCORES:'
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
    prompt = 'Retrieve the countries affected from these events taken from news headlines, numbered below:\n'
    for i, event in enumerate(news_headlines):
        prompt += f'\n{i+1}. {event}'
    response = GPT_Completion(prompt).get_response()

    current_number = 1
    countries = []
    for country in response.splitlines():
        if country.startswith(f'{current_number}. '):
            countries.append(country.removeprefix(f'{current_number}. ').split(','))
            current_number += 1
    return countries


# ---------------------------------------------------------------------------- #
#                                    Testing                                   #
# ---------------------------------------------------------------------------- #

news_headlines = ['Iran also barred from Nobel ceremony, after Russia, Belaru', 'Ship ports closed everywhere',
                  'Celebrity wins an oscar award', 'Famous person has died', 'Minor pandemic spreads to America']
real_events = ["Bolsonaro or Lula? U.S. Brazilians cast ballots in their home country's high-stakes runoff election", "Russia is suspending a Ukraine grain export deal that has helped keep food prices down", "World Series rainout, Astros-Phils to play Game 3 Tuesday", 'The Coronavirus Impact on Personal Finances', 'Tropical Depression Lisa crosses into southern Mexico']

print(rate_news_headlines(real_events))
print(retrieve_countries_from_headlines(real_events))