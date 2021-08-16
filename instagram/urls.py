from django.urls import path
from . import views

app_name = 'instagram'
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('post/', views.PostView.as_view(), name='post'),
]