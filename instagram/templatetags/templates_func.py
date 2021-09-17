from django import template
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