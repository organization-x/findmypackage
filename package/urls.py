from django.contrib import admin
from django.urls import path, include
from web.views import MainView, TrackView, AboutUsView, FaqView, ReviewsView

# We will use class based views for our web pages

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', MainView.as_view(), name='main'),
    path('track/', TrackView.as_view(), name='track'),
    path('about/', AboutUsView.as_view(), name='about'),
    path('faq/', FaqView.as_view(), name='faq'),
    path('reviews/', ReviewsView.as_view(), name='reviews'),
]
