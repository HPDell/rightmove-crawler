from django.urls import path
from property import views

urlpatterns = [
    path('property/', views.property_list),
    path('property/<int:pk>', views.property_detail)
]
