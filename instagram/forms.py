from typing import Text
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.core.files.base import File
from django.db.models import fields
from django.db.models.base import Model
from .models import CommentToPost, Message, Posts
from users.models import User


class PostForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea, label='', required=False)
    image = forms.ImageField(label='')
    tag = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Tag'}), required=False)

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    class Meta:
        model = Posts
        fields = ('text', 'image', 'tag')


class UserProfileUpdateForm(forms.ModelForm):
    username = forms.CharField(label='')
    name = forms.CharField(label='')
    text = forms.CharField(widget=forms.Textarea, label='')
    user_image = forms.ImageField(label='')

    def __init__(self, *args, **kwargs):
        super(UserProfileUpdateForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    class Meta:
        model = User
        fields = ('username', 'name', 'text', 'user_image',)


class CommentToPostForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea, label='')

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