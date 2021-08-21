from os import name
from django.db import models
from django.urls.base import translate_url
from django.utils import timezone
from users.models import User
import sys
sys.path.append('../')


class Posts(models.Model):
    text = models.TextField(max_length=200, null=True, blank=True)
    image = models.ImageField(upload_to='images/')
    tag = models.CharField(max_length=100, null=True, blank=True)
    post_date = models.DateTimeField(default=timezone.now(), null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    like_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Post'


class UserProfile(models.Model):
    username = models.CharField(max_length=150)
    text = models.CharField(max_length=300, null=True, blank=True)
    user_image = models.ImageField(upload_to='images/', null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'User Profile'

    def __str__(self):
        return self.username