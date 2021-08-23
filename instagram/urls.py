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
    path('comment_to_post/<int:pk>', views.CommentToPostView.as_view(), name='comment_to_post'),
    path('post_detail/<int:pk>', views.PostDetailView.as_view(), name='post_detail'),
    path('follow/<int:pk>', views.follow_view, name='follow'),
    path('unfollow/<int:pk>', views.unfollow_view, name='unfollow'),
    path('followee_list/<int:pk>/', views.FolloweeListView.as_view(), name='followee_list'),
]