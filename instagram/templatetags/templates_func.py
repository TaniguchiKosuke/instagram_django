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