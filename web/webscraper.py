from webbrowser import get
from bs4 import BeautifulSoup 
import requests

#p1 = WebScraper()
#p1.get_world_headlines()

class WebScraper:
    def __init__(self):
        self.headlines_url = 'https://apnews.com/hub/world-news'


    def get_world_headlines(self):
        world_news_response = requests.get(self.headlines_url) #You can change the url to the news site you want to use (make sure to change the specific tag as well)
        content = world_news_response.text                                      #This just isolates the text in the headline tag from all the actual code

        world_soup = BeautifulSoup(content, "lxml") 

        return world_soup.find_all('h2') #Locate Specific Headline Tag



    


