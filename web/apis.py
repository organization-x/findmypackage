import copy
import json
import logging
import re
import time
from enum import Enum

import requests
import xmltodict
from dateutil import parser
from dateutil.parser import ParserError
from django.utils import timezone
from package.settings import SECRETS

logger = logging.getLogger('fmp')

class DataMapper():
    def __init__(self, carrier, data):
        self.carrier = carrier
        self.data = data
        try:
            file = open('web/static/web/tracking_results_base.json')
            self.base = json.load(file)
            file.close()
        except FileNotFoundError:
            logger.warning("Couldn't load tracking_results_base.json")
        self.mapped_data = None

    def get_mapped_data(self):
        self.mapped_data = copy.deepcopy(self.base)
        if self.carrier is Carrier.fedex:
            return self.get_mapped_fedex_data()
        elif self.carrier is Carrier.usps:
            return self.get_mapped_usps_data()
        elif self.carrier is Carrier.dhl:
            return self.get_mapped_dhl_data()
        elif self.carrier is Carrier.ups:
            return self.get_mapped_ups_data()

    def get_mapped_fedex_data(self):
        if self.data.get('errors') is not None:
            return ERROR_MESSAGE

        self.data = self.data['output']['completeTrackResults'][0]
        if self.data['trackResults'][0].get('error') is not None:
            return {
                'trackingNumber': self.data['trackingNumber'],
                'errorMessage': self.data['trackResults'][0]['error']['message']
            }

        self.map_value(['carrier'], 'FedEx')
        self.map_value(['trackingNumber'], self.data['trackingNumber'])

        latestStatus = self.data['trackResults'][0]['latestStatusDetail']
        if latestStatus is not None:
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

        for i, event in enumerate(reversed(self.data['trackResults'][0]['scanEvents'] or [])):
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

        # FedEx has two different places for delivery date
        delivery_date_a = None
        dates = self.data['trackResults'][0].get('dateAndTimes', [{}])
        for date in dates:
            if date.get('type') != 'ESTIMATED_DELIVERY': continue
            delivery_date_a = date.get('dateTime')
            break

        delivery_time =  delivery_date_a or self.data['trackResults'][0].get('estimatedDeliveryTimeWindow', {}).get('window', {}).get('ends')
        self.map_value(['estimatedTimeArrival'], delivery_time, action=self.format_date)
        return self.mapped_data

    def get_mapped_usps_data(self):
        if self.data.get('Error') is not None:
            return ERROR_MESSAGE

        self.data = self.data.get('TrackResponse', {}).get('TrackInfo')
        if self.data.get('Error') is not None:
            return {
                'trackingNumber': self.data.get('@ID'),
                'errorMessage': 'Tracking number cannot be found. Please correct the tracking number and try again.'
            }

        self.map_value(['carrier'], 'USPS')
        self.map_value(['trackingNumber'], self.data.get('@ID'))

        statusSummary = self.data.get('StatusSummary')
        if statusSummary is not None:
            address = self.get_address_from_string(statusSummary)

            self.map_value(['currentStatus', 'status'],
                           self.data.get('Status'))
            self.map_value(['currentStatus', 'description'], " ".join(
                self.data.get('StatusSummary').split()[:-4]))
            self.map_value(['currentStatus', 'location', 'streetLines'], None)
            self.map_value(['currentStatus', 'location', 'city'],
                           address.get('city'), action=self.capitalize_string)
            self.map_value(['currentStatus', 'location', 'state'], address.get('state'))
            self.map_value(['currentStatus', 'location',
                            'postalCode'], address.get('postalCode'))
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

        for i, event in enumerate(self.data.get('TrackDetail') or []):
            self.mapped_data['events'].append(
                copy.deepcopy(self.mapped_data['eventTemplate']))
            self.map_value(['events', i, 'date'],
                           f"{event.get('EventDate')}, {event.get('EventTime')}")
            self.map_value(['events', i, 'description'], event.get('Event'))
            self.map_value(['events', i, 'location', 'streetLines'], None)
            self.map_value(['events', i, 'location', 'city'], event.get('EventCity'), action=self.capitalize_string)
            self.map_value(['events', i, 'location', 'state'],
                           event.get('EventState'))
            self.map_value(['events', i, 'location', 'postalCode'],
                           event.get('EventZIPCode'))
            self.map_value(['events', i, 'location', 'country'],
                           event.get('EventCountry'))
            self.map_value(['events', i, 'status'],
                           event.get('Event'))

        self.map_value(['estimatedTimeArrival'],
                       f"{self.data.get('ExpectedDeliveryDate') or ''} {self.data.get('ExpectedDeliveryTime') or ''}")
        return self.mapped_data

    def get_mapped_dhl_data(self):
        if self.data.get('title') is not None:
            return ERROR_MESSAGE

        self.data = self.data.get('shipments')[0]
        self.map_value(['carrier'], 'DHL')
        self.map_value(['trackingNumber'], self.data.get('id'))

        latestStatus = self.data.get('status')
        if latestStatus is not None:
            description = f"{latestStatus.get('remark') or ''} {latestStatus.get('nextSteps') or ''} {latestStatus.get('nextSteps') or ''}"
            self.map_value(['currentStatus', 'status'], latestStatus.get('statusCode'))
            self.map_value(['currentStatus', 'description'], description)
            self.map_value(['currentStatus', 'location', 'country'], latestStatus.get('location', {}).get('countryCode'))
            self.map_value(['currentStatus', 'location', 'postalCode'], latestStatus.get('location', {}).get('address', {}).get('postalCode'))
            self.map_value(['currentStatus', 'location', 'city'], latestStatus.get('location', {}).get('address', {}).get('addressLocality'), action=self.capitalize_string)
            self.map_value(['currentStatus', 'location', 'streetLines'], None)
            self.map_value(['currentStatus', 'location', 'country'], None)
            self.map_value(['currentStatus', 'delayDetail'], None)

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

        for i, event in enumerate(reversed(self.data.get('events') or [])):
            self.mapped_data['events'].append(
                copy.deepcopy(self.mapped_data['eventTemplate']))
            self.map_value(['events', i, 'date'], event.get(
                'timestamp'), action=self.format_date)
            self.map_value(['events', i, 'description'],
                           event.get('description'))
            self.map_value(['events', i, 'location', 'streetLines'], None)
            self.map_value(['events', i, 'location', 'state'], None)
            self.map_value(['events', i, 'location', 'city'], event.get('location', {}).get(
                'address', {}).get('addressLocality'), action=self.capitalize_string)
            self.map_value(['events', i, 'location', 'postalCode'], event.get(
                'location', {}).get('address', {}).get('postalCode'))
            self.map_value(['events', i, 'location', 'country'], event.get(
                'location', {}).get('address', {}).get('countryCode'))
            self.map_value(['events', i, 'status'], event.get('statusCode'))

        self.map_value(['estimatedTimeArrival'],
                       self.data.get('estimatedTimeOfDelivery'))
        return self.mapped_data

    def get_mapped_ups_data(self):
        if self.data.get('errors') is not None:
            return ERROR_MESSAGE

        self.data = self.data.get('trackResponse', {}).get('shipment', [{}])[0]
        if self.data.get('warnings') is not None:
            return ERROR_MESSAGE

        self.map_value(['carrier'], 'UPS')
        self.map_value(['trackingNumber'], self.data.get('inquiryNumber'))

        self.data = self.data.get('package', [{}])[0]

        currentStatus = self.data.get('activity', [{}])[0]
        if currentStatus is not None:
            status = currentStatus.get('status', {})
            location = currentStatus.get('location', {}).get('address', {})
            self.map_value(['currentStatus', 'status'], status.get('description'))
            self.map_value(['currentStatus', 'description'], None)
            self.map_value(['currentStatus', 'location', 'streetLines'], location.get('addressLine1'))
            self.map_value(['currentStatus', 'location', 'city'], location.get('city'), action=self.capitalize_string)
            self.map_value(['currentStatus', 'location', 'state'], location.get('stateProvince'))
            self.map_value(['currentStatus', 'location', 'postalCode'], location.get('postalCode'))
            self.map_value(['currentStatus', 'location', 'country'], location.get('country'))
            self.map_value(['currentStatus', 'delayDetail'], None)

        destination = self.data.get('packageAddress', [{}])[0].get('address', {})
        self.map_value(['destination', 'streetLines'], destination.get('addressLine1'))
        self.map_value(['destination', 'city'], destination.get('city'), action=self.capitalize_string)
        self.map_value(['destination', 'state'], destination.get('stateProvince'))
        self.map_value(['destination', 'postalCode'], destination.get('postalCode'))
        self.map_value(['destination', 'country'], destination.get('countryCode'))

        for i, event in enumerate(self.data.get('activity') or []):
            self.mapped_data['events'].append(
                copy.deepcopy(self.mapped_data['eventTemplate']))
            self.map_value(['events', i, 'date'], event.get('date'), action=self.format_date)
            self.map_value(['events', i, 'description'], None)
            self.map_value(['events', i, 'location', 'streetLines'], None)
            self.map_value(['events', i, 'location', 'city'], event.get('location', {}).get('address', {}).get('city'), action=self.capitalize_string)
            self.map_value(['events', i, 'location', 'state'], event.get('location', {}).get('address', {}).get('stateProvince'))
            self.map_value(['events', i, 'location', 'postalCode'], event.get('location', {}).get('address', {}).get('postalCode'))
            self.map_value(['events', i, 'location', 'country'], event.get('location', {}).get('address', {}).get('country'))
            self.map_value(['events', i, 'status'], event.get('status', {}).get('description'))

        delivery_date, delivery_time = self.data.get('deliveryDate', [{}])[0].get('date'), self.data.get('deliveryTime', {}).get('endTime')
        self.map_value(['estimatedTimeArrival'], f'{delivery_date} T {delivery_time}', action=self.format_date)
        return self.mapped_data

    def map_value(self, keys, value, action=None):
        if (not value or (type(value) == list and not value[0]) or (type(value) == str and not value.strip())):
            return
        dict = self.mapped_data
        for i, key in enumerate(keys):
            if i == len(keys) - 1:
                if action is not None:
                    dict[key] = action(value)
                else:
                    dict[key] = value
                return
            dict = dict[key]

    def capitalize_string(self, string):
        return string.title()

    def format_date(self, date):
        try:
            parsed_date = parser.parse(date)
            date = timezone.localtime(parsed_date) if not timezone.is_naive(parsed_date) else parsed_date
            return date.strftime("%B %-d, %Y, %-I:%M %p")
        except (TypeError, ParserError):
            return None

    def get_address_from_string(self, string):
        address = {'city': None, 'state': None, 'postalCode': None}

        string = string.split('.')[0].split(' in ')[-1].split(' on ')[0]
        string = re.sub(r'[^\w\s]', '', string)

        splitted = string.split(' ')
        for split in splitted:
            # check for postal number
            if split.isnumeric():
                address['postalCode'] = split
                splitted.remove(split)
                break
        state = splitted.pop()
        address['state'] = self.capitalize_string(state) if len(state) > 4 else state
        address['city'] = " ".join(splitted)
        return address


# FEDEX TESTING NUMBERS: 111111111111, 123456789012, 581190049992, 568838414941
class FedexAPI():
    access_token = None
    access_token_expire_date = None

    @staticmethod
    def generate_access_token():
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {'grant_type': 'client_credentials', 'client_id': SECRETS['FEDEX_ID'],
                'client_secret': SECRETS['FEDEX_SECRET']}
        oauth_url = 'https://apis.fedex.com/oauth/token'

        response = requests.post(oauth_url, data=data, headers=headers).json()
        FedexAPI.access_token = response.get('access_token')
        FedexAPI.access_token_expire_date = (
            time.time() + int(response.get('expires_in', '60')) - 60)

    @staticmethod
    def get_track_package_data(tracking_number):
        if FedexAPI.access_token is None or time.time() > FedexAPI.access_token_expire_date:
            FedexAPI.generate_access_token()
        try:
            headers = {
                'content-type': 'application/json',
                'authorization': f"Bearer { FedexAPI.access_token }",
                'x-locale': 'en_US'
            }
            url = 'https://apis.fedex.com/track/v1/trackingnumbers'
            request_body = {'trackingInfo': [{'trackingNumberInfo': {
                'trackingNumber': f"{tracking_number}"}}], 'includeDetailedScans': True}
            response = requests.post(url, data=json.dumps(request_body), headers=headers).json()
            return response if response is not None else ERROR_MESSAGE
        except requests.exceptions.RequestException as e:
            logger.warning(e)
            return ERROR_MESSAGE


# USPS TESTING NUMBERS: 9400136106074907356100 (Lukas')
class USPSApi():
    @staticmethod
    def get_track_package_data(tracking_number):
        try:
            url = 'https://secure.shippingapis.com/ShippingAPI.dll'
            params = {
                'API': 'TrackV2',
                'XML': f"""<TrackFieldRequest USERID="{SECRETS['USPS_ID']}"><Revision>1</Revision><ClientIp>122.3.3</ClientIp><SourceId>AI Camp</SourceId><TrackID ID="{tracking_number}"/></TrackFieldRequest>"""
            }
            return xmltodict.parse(requests.post(url, params=params).content)
        except requests.exceptions.RequestException as e:
            logger.warning(e)
            return ERROR_MESSAGE


# DHL TESING NUMBERS 00340434292135100186 7777777770
class DHLApi():
    @staticmethod
    def get_track_package_data(tracking_number):
        try:
            url = 'https://api-eu.dhl.com/track/shipments'
            querystring = ({"trackingNumber": tracking_number})
            headers = {'DHL-API-Key': SECRETS['DHL_SECRET']}
            response = requests.request(
                "GET", url, headers=headers, params=querystring)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(e)
            return ERROR_MESSAGE


# UPS TESING NUMBERS: 1Z689F0V0314879807
class UPSApi():
    @staticmethod
    def get_track_package_data(tracking_number):
        try:
            url = f"https://onlinetools.ups.com/track/v1/details/{tracking_number}"
            headers = {'AccessLicenseNumber': SECRETS['UPS_SECRET'], 'Username': SECRETS['UPS_USERNAME'], 'Password': SECRETS['UPS_PASSWORD']}
            response = requests.request(
                "GET", url, headers=headers)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(e)
            return ERROR_MESSAGE


class Carrier(Enum):
    fedex = FedexAPI
    usps = USPSApi
    dhl = DHLApi
    ups = UPSApi


ERROR_MESSAGE = {
    'trackingNumber': 'Invalid',
    'errorMessage': 'Tracking number cannot be found. Please correct the tracking number and try again.'
}
