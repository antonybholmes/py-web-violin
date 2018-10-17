from django.urls import path
from django.conf.urls import url
from django.urls import include
from api import views

urlpatterns = [
    path('about', views.about, name='about'),
    path('pdf', views.pdf, name='pdf'),
]
