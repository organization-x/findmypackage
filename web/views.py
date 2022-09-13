from django.shortcuts import render
from django.views.generic import TemplateView
import logging

# We will use class based views to render our templates

class MainView(TemplateView):
    def __init__(self):
        self.logger = logging.getLogger('fmp')
        self.template_name = 'index.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {})