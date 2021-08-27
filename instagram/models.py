from os import name
from django.db import models
from django.db.models.base import ModelState
from django.db.models.fields import related
from django.urls.base import translate_url
from django.utils import timezone
from users.models import User


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
    created_at = models.DateTimeField(default=timezone.now)


class CommentToPost(models.Model):
    text = models.CharField(max_length=300)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Posts, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.author


class FriendShip(models.Model):
    followee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower_friendships')
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followee_friendships')
    is_connected = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('followee', 'follower')

    def __str__(self):
        return f'{self.follower} follows {self.followee}'


class Message(models.Model):
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_to_user')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dm_from_user')
    text = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Message from {self.from_user} to {self.to_user}'