from typing import Text
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.core.files.base import File
from django.db import reset_queries
from django.db.models import fields
from django.db.models.base import Model
from .models import CommentToPost, Message, Posts
from users.models import User


class PostForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Text'}), label='', required=False)
    image = forms.ImageField(label='')
    tag = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Tag'}), required=False)

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    class Meta:
        model = Posts
        fields = ('text', 'image', 'tag')


class UpdatePostForm(forms.ModelForm):
    image = forms.ImageField(label='', widget=forms.FileInput)
    text = forms.CharField(label='', widget=forms.Textarea(attrs={'placeholder':'Text'}), required=False)
    tag = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Tag'}), required=False)
    
    def __init__(self, *args, **kwargs):
        super(UpdatePostForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    class Meta:
        model = Posts
        fields = ('image', 'text','tag')


class UserProfileUpdateForm(forms.ModelForm):
    user_image = forms.ImageField(label='', widget=forms.FileInput, required=False)
    username = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    name = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Name'}), required=False)
    text = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Bio'}),  label='', required=False)

    def __init__(self, *args, **kwargs):
        super(UserProfileUpdateForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    class Meta:
        model = User
        fields = ('user_image', 'username', 'name', 'text',)


class CommentToPostForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Comment'}), label='')

    def __init__(self, *args, **kwargs):
        super(CommentToPostForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    class Meta:
        model = CommentToPost
        fields = ('text',)


class MessageForm(forms.ModelForm):
    text = forms.CharField(label='')

    def __init__(self, *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    class Meta:
        model = Message
        fields = ('text',)


class CommentFromPostListForm(forms.Form):
    text = forms.CharField(label='')

    def __init__(self, *args, **kwargs):
        super(CommentFromPostListForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
            field.widget.attrs["name"] = "text"
            field.widget.attrs['placeholder'] = 'コメントを送る'