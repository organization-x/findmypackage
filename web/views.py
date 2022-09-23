from webbrowser import get
from django.views.generic import TemplateView
from django.shortcuts import render
from dateutil import parser
from enum import Enum
import xmltodict
import requests

import copy
import json
import logging


class MainView(TemplateView):
    def __init__(self):
        self.logger = logging.getLogger('fmp')
        self.template_name = 'index.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'carriers': Carrier._member_names_})


class TrackView(TemplateView):
    def __init__(self):
        self.logger = logging.getLogger('fmp')
        self.template_name = 'detail.html'
    
    def post(self, request, *args, **kwargs):
        carrier = Carrier[request.POST['carrier']]
        return render(
            request,
            self.template_name,
            DataMapper(
                carrier,
                carrier.value.get_track_package_data(
                    request.POST['tracking_id']
                ),
            ).get_mapped_data()
        )


class DataMapper():
    def __init__(self, carrier, data):
        self.logger = logging.getLogger('fmp')
        self.carrier = carrier
        self.data = data
        try:
            file = open('web/static/web/tracking_results_base.json')
            self.base = json.load(file)
            file.close()
        except:
            self.logger.warning("Couldn't load tracking_results_base.json")
        self.mapped_data = None

    def get_mapped_data(self):
        self.mapped_data = copy.deepcopy(self.base)
        if self.carrier is Carrier.fedex:
            return self.get_mapped_fedex_data()
        elif self.carrier is Carrier.usps:
            return self.get_mapped_usps_data()

    def get_mapped_fedex_data(self):
        if self.data.get('errors') is not None:
            return {
                'trackingNumber': 'Invalid',
                'errorMessage': 'Tracking number cannot be found. Please correct the tracking number and try again.'
            }

        self.data = self.data['output']['completeTrackResults'][0]
        if self.data['trackResults'][0].get('error') is not None:
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

        address = self.data['trackResults'][0].get('lastUpdatedDestinationAddress')
        if address is not None:
            self.map_value(['destination', 'streetLines'], address.get('streetLines'))
            self.map_value(['destination', 'city'], address.get('city'), action=self.capitalize_string)
            self.map_value(['destination', 'state'], address.get('stateOrProvinceCode', {}))
            self.map_value(['destination', 'postalCode'], address.get('postalCode', {}))
            self.map_value(['destination', 'country'], address.get('countryCode', {}))

        i = 0
        for event in reversed(self.data['trackResults'][0]['scanEvents']):
            self.mapped_data['events'].append(copy.deepcopy(self.mapped_data['eventTemplate']))
            self.map_value(['events', i, 'date'], event.get('date'), action=self.format_date)
            self.map_value(['events', i, 'description'], event.get('eventDescription'))
            self.map_value(['events', i, 'location', 'streetLines'], event.get('scanLocation', {}).get('streetLines'))
            self.map_value(['events', i, 'location', 'city'], event.get('scanLocation', {}).get('city'), action=self.capitalize_string)
            self.map_value(['events', i, 'location', 'state'], event.get('scanLocation', {}).get('stateOrProvinceCode'))
            self.map_value(['events', i, 'location', 'postalCode'], event.get('scanLocation', {}).get('postalCode'))
            self.map_value(['events', i, 'location','country'], event.get('scanLocation', {}).get('countryCode'))
            self.map_value(['events', i, 'status'], event.get('derivedStatus'))
            i += 1
        
        self.map_value(['estimatedTimeArrival'], self.data['trackResults'][0].get('estimatedDeliveryTimeWindow', {}).get('window'))
        return self.mapped_data

    def get_mapped_usps_data(self):
        self.data = self.data.get('TrackResponse', {}).get('TrackInfo')
        if self.data.get('Error') is not None:
            return {
                'trackingNumber': self.data.get('@ID'),
                'errorMessage': 'Tracking number cannot be found. Please correct the tracking number and try again.'
            }
        
        self.map_value(['trackingNumber'], self.data.get('@ID'))

        self.map_value(['currentStatus', 'status'], self.data.get('StatusCategory'))
        self.map_value(['currentStatus', 'description'], self.data.get('StatusSummary'))
        self.map_value(['currentStatus', 'location', 'streetLines'], None)
        self.map_value(['currentStatus', 'location', 'city'], None)
        self.map_value(['currentStatus', 'location', 'state'], None)
        self.map_value(['currentStatus', 'location', 'postalCode'], None)
        self.map_value(['currentStatus', 'location', 'country'], None)
        self.map_value(['currentStatus', 'delayDetail'], None)

        self.map_value(['destination', 'streetLines'], None)
        self.map_value(['destination', 'city'], self.data.get('DestinationCity'), action=self.capitalize_string)
        self.map_value(['destination', 'state'], self.data.get('DestinationState'))
        self.map_value(['destination', 'postalCode'], self.data.get('DestinationZip'))
        self.map_value(['destination', 'country'], 'US')

        i = 0
        for event in reversed(self.data.get('TrackDetail')):
            self.mapped_data['events'].append(copy.deepcopy(self.mapped_data['eventTemplate']))
            self.map_value(['events', i, 'date'], f"{event.get('EventDate')}, {event.get('EventTime')}")
            self.map_value(['events', i, 'description'], event.get('Event'))
            self.map_value(['events', i, 'location', 'streetLines'], None)
            self.map_value(['events', i, 'location', 'city'], event.get('EventCity'), action=self.capitalize_string)
            self.map_value(['events', i, 'location', 'state'], event.get('EventState'))
            self.map_value(['events', i, 'location', 'postalCode'], event.get('EventZIPCode'))
            self.map_value(['events', i, 'location','country'], event.get('EventCountry'))
            self.map_value(['events', i, 'status'], event.get('EventStatusCategory'))
            i += 1

        self.map_value(['estimatedTimeArrival'], f"{self.data.get('ExpectedDeliveryDate')}, {self.data.get('ExpectedDeliveryTime')}")
        return self.mapped_data

    def map_value(self, keys, value, action=None):
        if (not value or (type(value) == list and not value[0]) or value is None):
            return
        dict = self.mapped_data
        for i, key in enumerate(keys):
            if i is len(keys)-1:
                if action is not None:
                    dict[key] = action(value)
                else:
                    dict[key] = value
                return
            dict = dict[key]

    def capitalize_string(self, string):
        return string.title()

    def format_date(self, date):
        return parser.parse(date)


# FEDEX TESTING NUMBERS: 111111111111, 123456789012, 581190049992, 581190049992, 568838414941 
class FedexAPI():
    def get_access_token():
        headers = { "Content-Type" : "application/x-www-form-urlencoded" }
        data = {"grant_type": "client_credentials","client_id": "l7851e798fd0614154b2e2c5d701c8b656","client_secret": "a380512b3cd846daa8598845d5885beb"}
        oauth_url = "https://apis.fedex.com/oauth/token"
        return requests.post(oauth_url, data=data, headers=headers).json()['access_token']
    
    def get_track_package_data(tracking_number):
        headers = {
            'content-type': 'application/json',
            'authorization': f"Bearer { FedexAPI.get_access_token() }",
            'x-locale': 'en_US'
        }
        url = 'https://apis.fedex.com/track/v1/trackingnumbers'
        request_body = {"trackingInfo": [{"trackingNumberInfo": {"trackingNumber": f"{tracking_number}"}}],"includeDetailedScans": True}
        return requests.post(url, data=json.dumps(request_body), headers=headers).json()


# USPS TESTING NUMBERS: 4209070387179200190314774201833062
class USPSApi():
    def get_track_package_data(tracking_number):
        url = 'https://secure.shippingapis.com/ShippingAPI.dll'
        params = {
            'API': 'TrackV2',
            'XML': f"""<TrackFieldRequest USERID="829JEFF01013"><Revision>1</Revision><ClientIp>122.3.3</ClientIp><SourceId>AI Camp</SourceId><TrackID ID="{tracking_number}"/></TrackFieldRequest>"""
        }
        return xmltodict.parse(requests.post(url, params=params).content)


class Carrier(Enum):
    fedex = FedexAPI
    usps = USPSApi