from django.contrib import admin
from django.urls import path
from web.views import MainView

# We will use class based views for our web pages

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', MainView.as_view(), name='main'),
]
