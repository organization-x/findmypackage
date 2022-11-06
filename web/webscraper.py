from random import choices
from bs4 import BeautifulSoup 
import numpy as np
import pandas as pd
import requests
import os
import openai
from openai.embeddings_utils import get_embedding, cosine_similarity

world_news_response = requests.get("https://apnews.com/hub/world-news") #You can change the url to the news site you want to use (make sure to change the specific tag as well)
content = world_news_response.text                                      #This just isolates the text in the headline tag from all the actual code

world_soup = BeautifulSoup(content, "lxml") 

headlines = world_soup.find_all('h2') #Locate Specific Headline Tag
x = ""
for headline in headlines:
  x = x + headline.text + "  "

x = x.split("  ")
openai.api_key = "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"

embedding = openai.Embedding.create(
    input=x,
    engine="text-similarity-davinci-001"
)["data"][0]["embedding"]
len(embedding)

print(type(x))