from django.db import models
from django.utils import timezone


class Review(models.Model):
    author = models.CharField(max_length=30)
    stars = models.SmallIntegerField()
    content = models.TextField(max_length=300)
    date = models.DateField(default=timezone.now)