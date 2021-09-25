from os import name
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.base import ModelState, ModelStateFieldsCacheDescriptor
from django.db.models.deletion import CASCADE
from django.db.models.expressions import F
from django.db.models.fields import related
from django.urls.base import translate_url
from django.utils import timezone
from users.models import User


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Tag(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Posts(TimeStampedModel):
    text = models.TextField(max_length=200, null=True, blank=True)
    image = models.ImageField(upload_to='images/')
    tag = models.CharField(max_length=100, null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    like_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Post'
    
    def __str__(self):
        return f'posted by {self.author}'


class PostTagRelation(TimeStampedModel):
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE)
    post = models.ForeignKey('Posts', on_delete=models.CASCADE)


class PostLikes(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Posts, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} likes {self.post.author}'s post"


class CommentToPost(TimeStampedModel):
    text = models.CharField(max_length=300)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Posts, on_delete=models.CASCADE)
    comment_count = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.author} {self.text}'


class CommentToComment(TimeStampedModel):
    text = models.CharField(max_length=300)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    to_comment = models.ForeignKey(CommentToPost, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.author} {self.text}'


class PostCommentRelation(TimeStampedModel):
    comment_to_comment = models.ForeignKey(CommentToComment, on_delete=models.CASCADE)
    comment_to_post = models.ForeignKey(CommentToPost, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('comment_to_comment', 'comment_to_post')

    def __str__(self):
        return f'{self.comment_to_comment} and {self.comment_to_post}'



class FriendShip(TimeStampedModel):
    followee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower_friendships')
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followee_friendships')
    is_connected = models.BooleanField(default=False)

    class Meta:
        unique_together = ('followee', 'follower')

    def __str__(self):
        return f'{self.follower} follows {self.followee}'


class Message(TimeStampedModel):
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_to_user')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dm_from_user')
    text = models.CharField(max_length=300)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Message from {self.from_user} to {self.to_user}'


class PostSave(TimeStampedModel):
    post = models.ForeignKey(Posts, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} saved {self.post.author}'s post"


class FollowTag(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user} followed {self.tag}'