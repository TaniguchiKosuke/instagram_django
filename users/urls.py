from django.contrib import admin
from django.urls import path
from users import views

app_name = 'users'

urlpatterns = [
    path('signup/', views.CreateUser.as_view(), name='signup'),
    path('login/', views.UserLogin.as_view(), name='login'),
    path('logout/', views.user_logout, name='logout'),
]