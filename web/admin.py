from django.contrib import admin
from .models import Review, NewsHeadline

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('author', 'stars')

@admin.register(NewsHeadline)
class NewsHeadlineAdmin(admin.ModelAdmin):
    list_display = ('headline', 'impact_score', 'countries_affected')
    search_fields = ('headline', )
    ordering = ['-date']