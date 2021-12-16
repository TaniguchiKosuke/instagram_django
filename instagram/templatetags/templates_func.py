from django import template
import random
import datetime
from django.utils.timezone import localtime


# from ..models import PostLikes
register = template.Library()


@register.filter
def judge_following(request_user, followers):
    followers_list = []
    for follower in followers.all():
        followers_list.append(follower.username)
    if request_user.username in followers_list:
        return True
    else:
        return False


@register.filter
def judge_following_hashtag(user_profile, tag_name):
    from ..models import FollowTag
    following_tag = FollowTag.objects.filter(user=user_profile, tag__name=tag_name)
    if following_tag:
        return True
    else:
        return False


@register.filter
def judge_likes(user, post):
    #importの問題(循環importかな？)を回避するためにここでimport
    from ..models import PostLikes
    post_like = PostLikes.objects.filter(user=user).filter(post=post)
    if post_like:
        return True
    else:
        return False


@register.filter
def count_tag(tag_name):
    #importの問題(循環importかな？)を回避するためにここでimport
    from ..models import PostTagRelation
    tag_count = PostTagRelation.objects.filter(tag__name=tag_name).count()
    return tag_count


@register.filter
def split_tags(tag_str):
    """
    tagを#で分割してテンプレートにlistとして渡す
    """
    tags_list = tag_str.split('#')
    tag_list = []
    for tag in tags_list:
        tag = '#' + tag
        tag_list.append(tag)
    #tag_listの0番目の要素はただの＃だからこれを削除
    tag_list.pop(0)
    return tag_list


@register.filter
def count_comment(post):
    from ..models import CommentToPost
    comment_count = CommentToPost.objects.filter(post=post).count()
    return comment_count


@register.filter
def liked_post_user(post):
    from ..models import PostLikes
    post_likes = PostLikes.objects.filter(post=post)
    users = []
    for post_like in post_likes:
        users.append(post_like.user)
    if users:
        user = random.choice(users)
    else:
        return False
    return user


@register.filter
def judge_saved(user, post):
    from ..models import PostSave
    post_save = PostSave.objects.filter(user=user, post=post)
    if post_save:
        return True
    else:
        return False


@register.filter
def count_liked_user(post):
    from ..models import PostLikes
    post_likes = PostLikes.objects.filter(post=post).count()
    post_likes = post_likes -1
    return post_likes


@register.filter
def find_reccomended_user_follower(user, request_user):
    followers = user.followers.all()
    request_user_followees = request_user.followees.all()
    request_user_followees_list = []
    if request_user_followees and followers:
        for request_user_followee in request_user_followees:
            if request_user_followee in followers:
                request_user_followees_list.append(request_user_followee)
            else:
                continue
    if request_user_followees_list:
        reccomended_user_follower = random.choice(request_user_followees_list)
        return reccomended_user_follower
    else:
        return False
    


@register.filter
def count_reccomended_user_follower(user, request_user):
    request_user_followees = request_user.followees.all()
    reccomended_user_followers = user.followers.all()
    request_user_followees_list = []
    for request_user_followee in request_user_followees:
        if request_user_followee in reccomended_user_followers:
            request_user_followees_list.append(request_user_followee)
        else:
            continue
    user_count = len(request_user_followees_list) - 1
    return user_count


@register.filter
def comment_to_comment_count(comment_pk):
    from ..models import CommentToComment, CommentToPost
    to_comment = CommentToPost.objects.get(pk=comment_pk)
    comment_count = CommentToComment.objects.filter(to_comment=to_comment).count()
    return comment_count


@register.filter
def comment_date(comment_pk):
    from ..models import CommentToPost
    now_datetime = datetime.datetime.now()
    today = datetime.datetime.strftime(now_datetime, '%Y-%m-%d')
    comment_created_at = CommentToPost.objects.get(pk=comment_pk).created_at
    comment_created_at = localtime(comment_created_at)
    comment_date = datetime.datetime.strftime(comment_created_at, '%Y-%m-%d')
    if comment_date == today:
        now_datetime = datetime.datetime.strftime(now_datetime, '%Y%m%d%H')
        comment_created_at = datetime.datetime.strftime(comment_created_at, '%Y%m%d%H')
        comment_date = str(int(now_datetime)-int(comment_created_at)) + 'hours ago'
    return comment_date


@register.filter
def comment_to_comment_date(comment_pk):
    from ..models import CommentToComment
    now_datetime = datetime.datetime.now()
    today = datetime.datetime.strftime(now_datetime, '%Y-%m-%d')
    comment_created_at = CommentToComment.objects.get(pk=comment_pk).created_at
    comment_created_at = localtime(comment_created_at)
    comment_date = datetime.datetime.strftime(comment_created_at, '%Y-%m-%d')
    if comment_date == today:
        now_datetime = datetime.datetime.strftime(now_datetime, '%Y%m%d%H')
        comment_created_at = datetime.datetime.strftime(comment_created_at, '%Y%m%d%H')
        comment_date = str(int(now_datetime)-int(comment_created_at)) + 'hours ago'
    return comment_date