from webbrowser import get
from bs4 import BeautifulSoup 
import requests


def get_world_headlines():
    world_news_response = requests.get("https://apnews.com/hub/world-news") #You can change the url to the news site you want to use (make sure to change the specific tag as well)
    content = world_news_response.text                                      #This just isolates the text in the headline tag from all the actual code

    world_soup = BeautifulSoup(content, "lxml") 

    return world_soup.find_all('h2') #Locate Specific Headline Tag



    
