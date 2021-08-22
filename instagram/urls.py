from os import name
from django.urls import path
from . import views

app_name = 'instagram'
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('post/', views.PostView.as_view(), name='post'),
    path('user_profile/<int:pk>/', views.UserProfileView.as_view(), name='user_profile'),
    path('user_profile_update/<int:pk>/', views.UserProfileUpdateView.as_view(), name='user_profile_update'),
    path('like_post/<int:pk>/', views.like_post, name='like_post'),
]