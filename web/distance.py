import requests

import json
import os
from package.settings import SECRETS





def distanceCalc(loc1, loc2):
    url ="https://maps.googleapis.com/maps/api/distancematrix/json?"

    origin = loc1
    destination = loc2
    url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins=" + origin + "&destinations=" + destination + "&units=imperial&key=" + SECRETS['FMP_MAPS_KEY']

    payload={}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    parsed = json.loads(response.text)
    row = parsed["rows"]
    row = (row[0])
    elements = row['elements']
    info = elements[0]
    status = info["status"]
    if status=="ZERO_RESULTS":
        print("no distance")
    else:
        print(info["distance"]["text"])
        distance = info["distance"]["text"]
        index = distance.index(" ")
        distance = distance[0:index]
        distance = distance.replace(",","")
        distance = int(distance)
        relevance = 6.644-(0.007*distance)
        relevance = 2 ** relevance
        if relevance < 1:
            relevance = 0
        print(relevance)
