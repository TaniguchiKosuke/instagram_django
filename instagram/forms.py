from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.db.models import fields
from .models import CommentToPost, Message, Posts
from users.models import User


class PostForm(forms.ModelForm):

    class Meta:
        model = Posts
        fields = ('text', 'image', 'tag',)


class UserProfileUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('username', 'name', 'text', 'user_image',)


class CommentToPostForm(forms.ModelForm):

    class Meta:
        model = CommentToPost
        fields = ('text',)


class MessageForm(forms.ModelForm):

    class Meta:
        model = Message
        fields = ('text',)