from django.db import models

# Create your models here.
class Property(models.Model):
    """
    Property model
    """
    title = models.CharField(max_length=255)
    type_name = models.CharField(max_length=255)
    distance = models.FloatField()
    beds = models.PositiveSmallIntegerField()
    baths = models.PositiveSmallIntegerField()
    url = models.URLField()
    price_pcm = models.PositiveIntegerField()
    price_pw = models.PositiveIntegerField()
    available_date = models.DateField()
    deposit = models.PositiveIntegerField()
