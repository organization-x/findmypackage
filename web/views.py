import logging
import random

from django.db.models import Avg
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from package.settings import SECRETS

from .apis import Carrier, DataMapper
from .models import Review
from .gpt3 import calculate_delivery_delay


class MainView(TemplateView):
    def __init__(self):
        self.logger = logging.getLogger('fmp')
        self.template_name = 'index.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'error': request.GET.get('error')})


class TrackView(TemplateView):
    def __init__(self):
        self.logger = logging.getLogger('fmp')
        self.template_name = 'track.html'

    def post(self, request, *args, **kwargs):
        if request.POST['tracking_id']:
            for carrier in Carrier:
                data = DataMapper(
                    carrier,
                    carrier.value.get_track_package_data(
                        request.POST['tracking_id']
                    ),
                ).get_mapped_data()
                if data.get('errorMessage') is None:
                    data['calculated_delay'] = calculate_delivery_delay(data.get('currentStatus', {}).get('status'), data.get('currentStatus', {}).get('location'))
                    data['FMP_MAPS_KEY'] = SECRETS['FMP_MAPS_KEY']
                    return render(request, self.template_name, data)
        response = redirect('main')
        response['Location'] += '?error=True'
        return response


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
        reviews = Review.objects.all()
        reviews_list = list(reviews)
        context = {
            'reviews': random.sample(reviews_list, 10) if len(reviews_list) > 10 else random.sample(reviews_list, len(reviews_list)),
            'stars_average': reviews.aggregate(Avg('stars')).get('stars__avg'),
            'total_reviews_count': reviews.count(),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        Review.objects.create(author=request.POST['name'], stars=request.POST['stars'], content=request.POST['subject'])
        return redirect('reviews')
