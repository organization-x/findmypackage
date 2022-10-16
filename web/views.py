from django.views.generic import TemplateView
from django.shortcuts import render

import logging

from .apis import DataMapper, Carrier

from package.settings import SECRETS


class MainView(TemplateView):
    def __init__(self):
        self.logger = logging.getLogger('fmp')
        self.template_name = 'index.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'carriers': Carrier._member_names_})


class TrackView(TemplateView):
    def __init__(self):
        self.logger = logging.getLogger('fmp')
        self.template_name = 'track.html'
    
    def post(self, request, *args, **kwargs):
        data = {
            'trackingNumber': 'Invalid',
            'errorMessage': 'Tracking number cannot be found. Please correct the tracking number and try again.'
        }
        if request.POST['tracking_id']:
            for carrier in Carrier:
                data = DataMapper(
                    carrier,
                    carrier.value.get_track_package_data(
                        request.POST['tracking_id']
                    ),
                ).get_mapped_data()
                if data.get('errorMessage') is None:
                    break
        data['FMP_MAPS_KEY'] = SECRETS['FMP_MAPS_KEY']        
        return render(request, self.template_name, data)


class AboutUsView(TemplateView):
    def __init__(self):
        self.logger = logging.getLogger('fmp')
        self.template_name = 'aboutus.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {})


class FaqView(TemplateView):
    def __init__(self):
        self.logger = logging.getLogger('fmp')
        self.template_name = 'faq.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {})


class ReviewsView(TemplateView):
    def __init__(self):
        self.logger = logging.getLogger('fmp')
        self.template_name = 'review.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {})