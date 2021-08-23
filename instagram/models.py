from os import name
from django.db import models
from django.urls.base import translate_url
from django.utils import timezone
from users.models import User
# import sys
# sys.path.append('../')


class Posts(models.Model):
    text = models.TextField(max_length=200, null=True, blank=True)
    image = models.ImageField(upload_to='images/')
    tag = models.CharField(max_length=100, null=True, blank=True)
    post_date = models.DateTimeField(default=timezone.now, null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    like_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Post'


class PostLikes(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Posts, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class CommentToPost(models.Model):
    text = models.CharField(max_length=300)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Posts, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user