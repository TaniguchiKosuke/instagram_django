from os import name
from django.urls import path
from . import views

app_name = 'instagram'
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('post/', views.PostView.as_view(), name='post'),
    # path('post/', views.post_view, name='post'),
    path('user_profile/<int:pk>/', views.UserProfileView.as_view(), name='user_profile'),
    path('user_profile_update/<int:pk>/', views.UserProfileUpdateView.as_view(), name='user_profile_update'),
    path('like_post/<int:pk>/', views.like_post, name='like_post'),
    path('comment_to_post/<int:pk>', views.CommentToPostView.as_view(), name='comment_to_post'),
    path('post_detail/<int:pk>', views.PostDetailView.as_view(), name='post_detail'),
    path('follow/<int:pk>', views.follow_view, name='follow'),
    path('unfollow/<int:pk>', views.unfollow_view, name='unfollow'),
    path('followee_list/<int:pk>/', views.FolloweeListView.as_view(), name='followee_list'),
    path('follower_list/<int:pk>/', views.FollowerListView.as_view(), name='follower_list'),
    path('messages/<int:pk>/', views.MessagesView.as_view(), name='messages'),
    path('message_list', views.MessageListView.as_view(), name='message_list'),
    path('tag_post_list/<str:tag>', views.TagPostListView.as_view(), name='tag_post_list'),
    path('comment_from_post_list/<int:pk>/', views.comment_from_post_list, name='comment_from_post_list'),
    path('search_friends/', views.SearchFriendsView.as_view(), name='search_friends'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('reccomended_posts/', views.ReccomendedPostsView.as_view(), name='reccomended_posts'),
    path('delete_post/<int:pk>/', views.DeletePostView.as_view(), name='delete_post'),
    path('update_post/<int:pk>/', views.UpdatePostView.as_view(), name='update_post'),
    path('see_all_reccomended_users/', views.SeeAllReccomendedUsersView.as_view(), name='see_all_reccomended_users'),
    path('liked_post_list/', views.LikedPostListView.as_view(), name='liked_post_list'),
    path('delete_comment/<int:pk>/', views.DeleteCommentView.as_view(), name='delete_comment'),
    path('liked_post_user/<int:pk>/', views.LikedPostUserView.as_view(), name='liked_post_user'),
    path('save_post/<int:pk>/', views.save_post, name='save_post')
]