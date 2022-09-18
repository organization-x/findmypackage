from django.shortcuts import render
from django.views.generic import TemplateView
import logging
import requests
import json

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
        return render(request, self.template_name, FedexPackage(request.POST['tracking_id']).get_prettified_json())
        

# TESTING NUMBERS: 111111111111, 123456789012, 581190049992, 581190049992, 568838414941  
class FedexPackage():
    def __init__(self, tracking_number):
        self.tracking_id = tracking_number

    def get_prettified_json(self):
        data = FedexAPI.get_track_package_data(FedexAPI.get_access_token(), self.tracking_id)['output']['completeTrackResults'][0]
        if not data['trackResults'][0].get('error') == None:
            return {
                'trackingNumber': data['trackingNumber'],
                'errorMessage': data['trackResults'][0]['error']['message']
            }
        return {
            'trackingNumber': data['trackingNumber'],
            'currentStatus': data['trackResults'][0]['latestStatusDetail'],
            'events': data['trackResults'][0]['scanEvents'],
            'ETA': data['trackResults'][0]['estimatedDeliveryTimeWindow'],
        }


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