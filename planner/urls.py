from django.urls import path
from planner import views

app_name = 'planner'

urlpatterns = [
    path('', views.index, name="index"),
]