from django.contrib import admin
from .models import Property

# Register your models here.

class AdminProperty(admin.ModelAdmin):
    list_display = ('title', 'type_name', 'beds', 'baths', 'price_pcm')

admin.site.register(Property, AdminProperty)