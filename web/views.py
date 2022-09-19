from django.shortcuts import render
from django.views.generic import TemplateView

from dateutil import parser
import logging
import requests
import json
import copy

# We will use class based views to render our templates

class MainView(TemplateView):
    def __init__(self):
        self.logger = logging.getLogger('fmp')
        self.template_name = 'index.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {})


class TrackView(TemplateView):
    def __init__(self):
        self.logger = logging.getLogger('fmp')
        self.template_name = 'detail.html'
    
    def post(self, request, *args, **kwargs):
        return render(
            request,
            self.template_name,
            DataMapper(
                'fedex',
                FedexAPI.get_track_package_data(FedexAPI.get_access_token(),
                request.POST['tracking_id'])
            ).get_mapped_data()
        )
        
 
class DataMapper():
    def __init__(self, carrier, data):
        self.carrier = carrier
        self.data = data
        try:
            file = open('web/static/web/tracking_results_base.json')
            self.base = json.load(file)
            file.close()
        except:
            print("Something went wrong?")
    
    def get_mapped_data(self):
        if self.carrier == 'fedex':
            return self.get_mapped_fedex_data()

    def get_mapped_fedex_data(self):
        self.data = self.data['output']['completeTrackResults'][0]

        if not self.data['trackResults'][0].get('error') == None:
            return {
                'trackingNumber': self.data['trackingNumber'],
                'errorMessage': self.data['trackResults'][0]['error']['message']
            }

        self.map_value(['trackingNumber'], self.data['trackingNumber'])

        latestStatus = self.data['trackResults'][0]['latestStatusDetail']
        self.map_value(['currentStatus', 'status'], latestStatus.get('statusByLocale'))
        self.map_value(['currentStatus', 'description'], latestStatus.get('description'))
        self.map_value(['currentStatus', 'location', 'streetLines'], latestStatus.get('scanLocation', {}).get('streetLines'))
        self.map_value(['currentStatus', 'location', 'city'], latestStatus.get('scanLocation', {}).get('city'), action=self.capitalize_string)
        self.map_value(['currentStatus', 'location', 'state'], latestStatus.get('scanLocation', {}).get('stateOrProvinceCode'))
        self.map_value(['currentStatus', 'location', 'postalCode'], latestStatus.get('scanLocation', {}).get('postalCode'))
        self.map_value(['currentStatus', 'location', 'country'], latestStatus.get('scanLocation', {}).get('countryCode'))
        self.map_value(['currentStatus', 'delayDetail'], latestStatus.get('delayDetail', {}).get('status'))

        i = 0
        for event in reversed(self.data['trackResults'][0]['scanEvents']):
            self.base['events'].append(copy.deepcopy(self.base['eventTemplate']))
            self.map_value(['events', i, 'date'], event.get('date'), action=self.format_date)
            self.map_value(['events', i, 'description'], event.get('eventDescription'))
            self.map_value(['events', i, 'location', 'streetLines'], event.get('scanLocation', {}).get('streetLines'))
            print('Street Lines:', event.get('scanLocation', {}).get('streetLines'))
            self.map_value(['events', i, 'location', 'city'], event.get('scanLocation', {}).get('city'), action=self.capitalize_string)
            self.map_value(['events', i, 'location', 'state'], event.get('scanLocation', {}).get('stateOrProvinceCode'))
            self.map_value(['events', i, 'location', 'postalCode'], event.get('scanLocation', {}).get('postalCode'))
            self.map_value(['events', i, 'location','country'], event.get('scanLocation', {}).get('countryCode'))
            self.map_value(['events', i, 'status'], event.get('derivedStatus'))
            print(self.base['events'][i]['location']['streetLines'])
            i += 1
        
        self.map_value(['estimatedTimeArrival'], self.data['trackResults'][0].get('estimatedDeliveryTimeWindow', {}).get('window'))
        print(self.base)
        return self.base

    def map_value(self, keys, value, action=None):
        if (not value or (type(value) == list and not value[0])):
            return
        dict = self.base
        for i, key in enumerate(keys):
            if i is len(keys)-1:
                if action is not None:
                    dict[key] = action(value)
                else:
                    dict[key] = value
                return
            dict = dict[key]

    def capitalize_string(self, string):
        return string.capitalize()

    def format_date(self, date):
        return parser.parse(date)


# FEDEX TESTING NUMBERS: 111111111111, 123456789012, 581190049992, 581190049992, 568838414941 
class FedexAPI():
    def get_access_token():
        headers = { "Content-Type" : "application/x-www-form-urlencoded" }
        data = {"grant_type": "client_credentials","client_id": "l7851e798fd0614154b2e2c5d701c8b656","client_secret": "a380512b3cd846daa8598845d5885beb"}
        oauth_url = "https://apis.fedex.com/oauth/token"
        return requests.post(oauth_url, data=data, headers=headers).json()['access_token']
    
    def get_track_package_data(access_token, tracking_number):
        headers = {
            'content-type': 'application/json',
            'authorization': f"Bearer { access_token }",
            'x-locale': 'en_US'
        }
        url = 'https://apis.fedex.com/track/v1/trackingnumbers'
        request_body = {"trackingInfo": [{"trackingNumberInfo": {"trackingNumber": f"{tracking_number}"}}],"includeDetailedScans": True}
        return requests.post(url, data=json.dumps(request_body), headers=headers).json()