from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.db.models import fields
from .models import Posts


class PostForm(forms.ModelForm):

    class Meta:
        model = Posts
        fields = ('text', 'image', 'tag',)