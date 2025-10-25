from django.urls import path
from planner import views

app_name = 'planner'

urlpatterns = [
    path('', views.index, name="index"),
    path('events/<slug:event_slug>/', views.view_event, name="view_event"),
    path('venue/<slug:venue_slug>/', views.view_venue, name="view_venue"),
    path('register/', views.register, name="register"),
    path('login/', views.login, name="login"),
    path('logout/', views.logout, name="logout"),
]