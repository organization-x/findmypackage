import copy
import json
import logging
import re
import time
from enum import Enum

import requests
import xmltodict
from dateutil import parser

from package.settings import SECRETS


class DataMapper():
    def __init__(self, carrier, data):
        self.logger = logging.getLogger('fmp')
        self.carrier = carrier
        self.data = data
        try:
            file = open('web/static/web/tracking_results_base.json')
            self.base = json.load(file)
            file.close()
        except FileNotFoundError:
            self.logger.warning("Couldn't load tracking_results_base.json")
        self.mapped_data = None

    def get_mapped_data(self):
        self.mapped_data = copy.deepcopy(self.base)
        if self.carrier is Carrier.fedex:
            return self.get_mapped_fedex_data()
        elif self.carrier is Carrier.usps:
            return self.get_mapped_usps_data()
        elif self.carrier is Carrier.dhl:
            return self.get_mapped_dhl_data()

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

        self.map_value(['carrier'], 'FedEx')
        self.map_value(['trackingNumber'], self.data['trackingNumber'])

        latestStatus = self.data['trackResults'][0]['latestStatusDetail']
        self.map_value(['currentStatus', 'status'],
                       latestStatus.get('statusByLocale'))
        self.map_value(['currentStatus', 'description'],
                       latestStatus.get('description'))
        self.map_value(['currentStatus', 'location', 'streetLines'],
                       latestStatus.get('scanLocation', {}).get('streetLines'))
        self.map_value(['currentStatus', 'location', 'city'], latestStatus.get(
            'scanLocation', {}).get('city'), action=self.capitalize_string)
        self.map_value(['currentStatus', 'location', 'state'], latestStatus.get(
            'scanLocation', {}).get('stateOrProvinceCode'))
        self.map_value(['currentStatus', 'location', 'postalCode'],
                       latestStatus.get('scanLocation', {}).get('postalCode'))
        self.map_value(['currentStatus', 'location', 'country'],
                       latestStatus.get('scanLocation', {}).get('countryCode'))
        self.map_value(['currentStatus', 'delayDetail'],
                       latestStatus.get('delayDetail', {}).get('status'))

        address = self.data['trackResults'][0].get(
            'lastUpdatedDestinationAddress')
        if address is not None:
            self.map_value(['destination', 'streetLines'],
                           address.get('streetLines'))
            self.map_value(['destination', 'city'], address.get(
                'city'), action=self.capitalize_string)
            self.map_value(['destination', 'state'],
                           address.get('stateOrProvinceCode', {}))
            self.map_value(['destination', 'postalCode'],
                           address.get('postalCode', {}))
            self.map_value(['destination', 'country'],
                           address.get('countryCode', {}))

        i = 0
        for event in reversed(self.data['trackResults'][0]['scanEvents']):
            self.mapped_data['events'].append(
                copy.deepcopy(self.mapped_data['eventTemplate']))
            self.map_value(['events', i, 'date'], event.get(
                'date'), action=self.format_date)
            self.map_value(['events', i, 'description'],
                           event.get('eventDescription'))
            self.map_value(['events', i, 'location', 'streetLines'], event.get(
                'scanLocation', {}).get('streetLines'))
            self.map_value(['events', i, 'location', 'city'], event.get(
                'scanLocation', {}).get('city'), action=self.capitalize_string)
            self.map_value(['events', i, 'location', 'state'], event.get(
                'scanLocation', {}).get('stateOrProvinceCode'))
            self.map_value(['events', i, 'location', 'postalCode'],
                           event.get('scanLocation', {}).get('postalCode'))
            self.map_value(['events', i, 'location', 'country'],
                           event.get('scanLocation', {}).get('countryCode'))
            self.map_value(['events', i, 'status'], event.get('derivedStatus'))
            i += 1

        self.map_value(['estimatedTimeArrival'], self.data['trackResults'][0].get(
            'estimatedDeliveryTimeWindow', {}).get('window'))
        return self.mapped_data

    def get_mapped_dhl_data(self):
        if self.data.get('title') is not None:
            return {
                'trackingNumber': 'Invalid',
                'errorMessage': 'Tracking number cannot be found. Please correct the tracking number and try again.'
            }
        self.data = self.data.get('shipments')[0]
        self.map_value(['carrier'], 'DHL')
        self.map_value(['trackingNumber'], self.data.get('id'))
        # current status vvv
        latestStatus = self.data.get('status')

        fullStat = ""
        stat = latestStatus.get('status')
        stat2 = latestStatus.get('statusCode')
        if stat is not None:
            fullStat = fullStat + stat
        if stat2 is not None:
            fullStat = stat2 + " / " + fullStat
        self.map_value(['currentStatus', 'status'], fullStat)
        remark = latestStatus.get('remark')
        nextSteps = latestStatus.get('nextSteps')
        fullDesc = latestStatus.get("description")
        if remark is not None:
            fullDesc = fullDesc + remark
        if nextSteps is not None:
            fullDesc = fullDesc + nextSteps
        self.map_value(['currentStatus', 'description'], fullDesc)
        loc = latestStatus.get('location')
        if loc is not None:
            # city = address[0:address.index('- ')]
            # country = address[address.index('-')+2:len(address)]
            address = loc.get('address')
            countryCode = address.get('countryCode')
            postal = address.get('postalCode')
            self.map_value(
                ['currentStatus', 'location', 'country'], countryCode)
            self.map_value(['currentStatus', 'location', 'postalCode'], postal)
            self.map_value(['currentStatus', 'location', 'city'], address.get(
                'addressLocality'), action=self.capitalize_string)
            self.map_value(['currentStatus', 'location', 'streetLines'], None)
            self.map_value(['events', 'location', 'state'], None)
            self.map_value(['currentStatus', 'delayDetail'], None)
        # destination info vvvv

        destination = self.data.get('destination')
        if destination is not None:
            address = destination.get('address')
            self.map_value(['destination', 'streetLines'], None)
            self.map_value(['destination', 'city'], address.get(
                'addressLocality'), action=self.capitalize_string)
            self.map_value(['destination', 'state'], None)
            self.map_value(['destination', 'postalCode'],
                           address.get("postalCode"))
            self.map_value(['destination', 'country'],
                           address.get('countryCode'))

        # events vvvv
        i = 0
        for event in reversed(self.data.get('events')):
            self.mapped_data['events'].append(
                copy.deepcopy(self.mapped_data['eventTemplate']))
            self.map_value(['events', i, 'date'], event.get(
                'timestamp'), action=self.format_date)
            self.map_value(['events', i, 'description'],
                           event.get('description'))
            remark = event.get('remark')
            nextSteps = event.get('nextSteps')
            fullDesc = event.get("description")
            if remark is not None:
                fullDesc = fullDesc + remark
            if nextSteps is not None:
                fullDesc = fullDesc + nextSteps
            self.map_value(['events', i, 'description'], fullDesc)
            self.map_value(['events', i, 'location', 'streetLines'], None)
            self.map_value(['events', i, 'location', 'state'], None)
            self.map_value(['events', i, 'location', 'city'], event.get('location', {}).get(
                'address', {}).get('addressLocality', {}), action=self.capitalize_string)
            self.map_value(['events', i, 'location', 'postalCode'], event.get(
                'location', {}).get('address', {}).get('postalCode', {}))
            self.map_value(['events', i, 'location', 'country'], event.get(
                'location', {}).get('address', {}).get('countryCode', {}))
            fullStat1 = ""
            stat = event.get('status')
            stat2 = event.get('statusCode')
            if stat is not None:
                fullStat1 = fullStat + stat
            elif stat2 is not None:
                fullStat1 = fullStat + stat2
            self.map_value(['events', i, 'status'], fullStat1)
            i += 1

        self.map_value(['estimatedTimeArrival'],
                       f"{self.data.get('estimatedTimeOfDelivery')}, {self.data.get('estimatedTimeOfDeliveryRemark')}")
        return self.mapped_data

    def get_mapped_usps_data(self):
        self.data = self.data.get('TrackResponse', {}).get('TrackInfo')
        if self.data.get('Error') is not None:
            return {
                'trackingNumber': self.data.get('@ID'),
                'errorMessage': 'Tracking number cannot be found. Please correct the tracking number and try again.'
            }

        self.map_value(['carrier'], 'USPS')
        self.map_value(['trackingNumber'], self.data.get('@ID'))

        statusSummary = self.data.get('StatusSummary')
        location = [re.sub(r'[^\w\s]', '', item)
                    for item in statusSummary.split()[-3:]]

        self.map_value(['currentStatus', 'status'],
                       self.data.get('StatusCategory'))
        self.map_value(['currentStatus', 'description'], " ".join(
            self.data.get('StatusSummary').split()[:-4]))
        self.map_value(['currentStatus', 'location', 'streetLines'], None)
        self.map_value(['currentStatus', 'location', 'city'],
                       location[0], action=self.capitalize_string)
        self.map_value(['currentStatus', 'location', 'state'], location[1])
        self.map_value(['currentStatus', 'location',
                       'postalCode'], location[2])
        self.map_value(['currentStatus', 'location', 'country'], 'US')
        self.map_value(['currentStatus', 'delayDetail'], None)

        self.map_value(['destination', 'streetLines'], None)
        self.map_value(['destination', 'city'], self.data.get(
            'DestinationCity'), action=self.capitalize_string)
        self.map_value(['destination', 'state'],
                       self.data.get('DestinationState'))
        self.map_value(['destination', 'postalCode'],
                       self.data.get('DestinationZip'))
        self.map_value(['destination', 'country'], 'US')

        i = 0
        for event in reversed(self.data.get('TrackDetail')):
            self.mapped_data['events'].append(
                copy.deepcopy(self.mapped_data['eventTemplate']))
            self.map_value(['events', i, 'date'],
                           f"{event.get('EventDate')}, {event.get('EventTime')}")
            self.map_value(['events', i, 'description'], event.get('Event'))
            self.map_value(['events', i, 'location', 'streetLines'], None)
            self.map_value(['events', i, 'location', 'city'], event.get(
                'EventCity'), action=self.capitalize_string)
            self.map_value(['events', i, 'location', 'state'],
                           event.get('EventState'))
            self.map_value(['events', i, 'location', 'postalCode'],
                           event.get('EventZIPCode'))
            self.map_value(['events', i, 'location', 'country'],
                           event.get('EventCountry'))
            self.map_value(['events', i, 'status'],
                           event.get('EventStatusCategory'))
            i += 1

        self.map_value(['estimatedTimeArrival'],
                       f"{self.data.get('ExpectedDeliveryDate')}, {self.data.get('ExpectedDeliveryTime')}")
        return self.mapped_data

    def map_value(self, keys, value, action=None):
        if (not value or (type(value) == list and not value[0]) or value is None):
            return
        dict = self.mapped_data
        for i, key in enumerate(keys):
            if i is len(keys) - 1:
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
    access_token = None
    access_token_expire_date = None

    @staticmethod
    def generate_access_token():
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "client_credentials", "client_id": SECRETS['FEDEX_ID'],
                "client_secret": SECRETS['FEDEX_SECRET']}
        oauth_url = "https://apis.fedex.com/oauth/token"

        response = requests.post(oauth_url, data=data, headers=headers).json()
        FedexAPI.access_token = response.get('access_token')
        FedexAPI.access_token_expire_date = (
            time.time() + int(response.get('expires_in', '60')) - 60)

    @staticmethod
    def get_track_package_data(tracking_number):
        if FedexAPI.access_token is None or time.time() > FedexAPI.access_token_expire_date:
            FedexAPI.generate_access_token()
        headers = {
            'content-type': 'application/json',
            'authorization': f"Bearer { FedexAPI.access_token }",
            'x-locale': 'en_US'
        }
        url = 'https://apis.fedex.com/track/v1/trackingnumbers'
        request_body = {"trackingInfo": [{"trackingNumberInfo": {
            "trackingNumber": f"{tracking_number}"}}], "includeDetailedScans": True}
        return requests.post(url, data=json.dumps(request_body), headers=headers).json()


# USPS TESTING NUMBERS: NONE
class USPSApi():
    @staticmethod
    def get_track_package_data(tracking_number):
        url = 'https://secure.shippingapis.com/ShippingAPI.dll'
        params = {
            'API': 'TrackV2',
            'XML': f"""<TrackFieldRequest USERID="{SECRETS['USPS_ID']}"><Revision>1</Revision><ClientIp>122.3.3</ClientIp><SourceId>AI Camp</SourceId><TrackID ID="{tracking_number}"/></TrackFieldRequest>"""
        }
        return xmltodict.parse(requests.post(url, params=params).content)

# DHL TESING NUMBERS 00340434292135100186 7777777770


class DHLApi():
    @staticmethod
    def get_track_package_data(tracking_number):
        url = 'https://api-eu.dhl.com/track/shipments'
        querystring = ({"trackingNumber": tracking_number})
        headers = {'DHL-API-Key': SECRETS['DHL_SECRET']}
        response = requests.request(
            "GET", url, headers=headers, params=querystring)
        return response.json()


class Carrier(Enum):
    fedex = FedexAPI
    usps = USPSApi
    dhl = DHLApi