from django.db import models
from django.utils import timezone


class Review(models.Model):
    author = models.CharField(max_length=30)
    stars = models.SmallIntegerField()
    content = models.TextField(max_length=300)

class NewsHeadline(models.Model):
    headline = models.TextField()
    date = models.DateTimeField()
    impact_score = models.SmallIntegerField(default=-1)
    countries_affected = models.TextField(default="{'countries': ['Nowhere']}")