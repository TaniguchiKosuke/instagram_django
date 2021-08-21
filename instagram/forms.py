from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.db.models import fields
from .models import Posts
from users.models import User


class PostForm(forms.ModelForm):

    class Meta:
        model = Posts
        fields = ('text', 'image', 'tag',)


class UserProfileUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('username', 'name', 'text', 'user_image',)