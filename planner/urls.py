from django.urls import path
from planner import views

app_name = 'planner'

urlpatterns = [
    path('', views.index, name="index"),
    path('dashboard/', views.dashboard, name="dashboard"), 
    path('events/<slug:event_slug>/', views.view_event, name="view_event"),
    path('venue/<slug:venue_slug>/', views.view_venue, name="view_venue"),
    path('register/', views.user_register, name="register"),
    path('login/', views.user_login, name="login"),
    path('logout/', views.user_logout, name="logout"),
    path('event/create/', views.create_event, name='create_event'),
]
