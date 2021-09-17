from django import template

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
def judge_likes(user, post):
    #importの問題(循環importかな？)を回避するためにここでimport
    from ..models import PostLikes
    post_like = PostLikes.objects.filter(user=user).filter(post=post)
    if post_like:
        return True
    else:
        return False