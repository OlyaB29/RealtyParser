from django.urls import path, include
from . import views


app_name = 'realty_app'


urlpatterns = [
    path('info', views.info, name='info'),

]

