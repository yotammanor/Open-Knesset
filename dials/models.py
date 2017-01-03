from django.db import models

class Dial(models.Model):
    precent = models.IntegerField(default=0)
    slug = models.SlugField(max_length=1000)
    description = models.TextField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
