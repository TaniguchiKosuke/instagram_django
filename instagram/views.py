import math
from os import name
import random
from django import contrib
from django.core.checks import messages
from django.core.files.base import ContentFile
from django.db.models import fields, query
from django.db.models.signals import post_save
from django.forms.utils import pretty_name, to_current_timezone
from django.http import request
from django.views.generic.base import TemplateView
from users.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.urls.base import reverse, translate_url
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import CommentToComment, CommentToPost, FollowTag, FriendShip, Message, PostLikes, PostSave, PostTagRelation, Posts, Tag
from .forms import CommentFromPostListForm, MessageForm, PostForm, UserProfileUpdateForm, CommentToPostForm, UpdatePostForm, CommentToCommentForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from itertools import chain
from operator import attrgetter
import datetime


class HomeView(LoginRequiredMixin, ListView):
    template_name = 'home.html'
    queryset = Posts
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        request_user = self.request.user
        #投稿を検索する処理
        following_tag = FollowTag.objects.filter(user=request_user)
        query = self.request.GET.get('query')
        if query:
            if not query.startswith('#'):
                queryset = Posts.objects.filter(Q(text__icontains=query) | Q(author__username__icontains=query) | Q(tag__icontains=query))
            elif query.startswith('#'):
                # queryset = Tag.objects.filter(Q(name__icontains=query))
                post_tag_relation = PostTagRelation.objects.filter(tag__name__icontains=query)
                post_tag_list = []
                for post_tag in post_tag_relation:
                    if not post_tag.tag in post_tag_list:
                        post_tag_list.append(post_tag.tag)
                    else:
                        continue
                queryset = post_tag_list
        #フォローしているユーザーがいる場合、もしくはフォローしているハッシュタグが存在する場合は、それらを考慮に入れておすすめの投稿を表示する
        elif request_user.followees.all() or following_tag:
            queryset = get_timeline_post(request_user)
        else:
            queryset = Posts.objects.all().order_by('-created_at')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        followee_friendships = FriendShip.objects.filter(follower__username=user)
        follower_friendships = FriendShip.objects.filter(followee__username=user)
        followee_count = followee_friendships.count()
        tag_follow_count = FollowTag.objects.filter(user=user).count()
        context['followee'] = followee_count + tag_follow_count
        context['follower'] = follower_friendships.count()
        context['comment_from_post_list_form'] = CommentFromPostListForm()
        query = self.request.GET.get('query')
        if query:
            context['query_exist'] = True
            if query.startswith('#'):
                context['query'] = query
                context['tags'] = PostTagRelation.objects.filter(tag__name__icontains=query)
            else:
                context['query'] = query
                context['is_not_tag'] = True
                post_list = Posts.objects.filter(Q(text__icontains=query) | Q(author__username__icontains=query) | Q(tag__icontains=query))
                if post_list:
                    context['first_post'] = post_list.first()

        #「知り合いかも」にフォローしてる、もしくはフォローされてる友達のフォローしてる人をおすすめとして表示させるための処理
        reccomended_users = find_reccomended_users(user, followee_friendships, follower_friendships)
        #reccomended_usersをシャッフルする処理
        if len(reccomended_users) < 1:
            reccomended_users = reccomended_users
        elif len(reccomended_users) < 2:
            reccomended_users = random.sample(reccomended_users, 1)
        elif len(reccomended_users) < 3:
            reccomended_users = random.sample(reccomended_users, 2)
        elif len(reccomended_users) < 4:
            reccomended_users = random.sample(reccomended_users, 3)
        else:
            reccomended_users = random.sample(reccomended_users, 4)
        context['reccomended_users'] = reccomended_users

        #今日メッセージを受け取っていたら、ホーム画面に通知する処理
        messages = Message.objects.filter(to_user=user)
        if messages:
            today = datetime.datetime.today().strftime('%Y-%m-%d')
            for message in messages:
                message_created_at = message.created_at.strftime('%Y-%m-%d')
                if message_created_at == today:
                    context['message_notice_today'] = True
        return context


def get_timeline_post(request_user):
    """
    タイムラインに表示させる投稿を取得する関数
    （フォローしてるユーザ―がいる場合、
    もしくはフォローしているハッシュタグがある場合）
    sort条件(
        フォローしているユーザーの投稿,
        フォローしているハッシュタグの投稿,
        自分の投稿,
        その他の投稿,
    )

    return: list
    """
    following_tags = FollowTag.objects.filter(user=request_user)
    followees = request_user.followees.all()
    if followees:
        for followee in followees:
            friend_and_my_posts = Posts.objects.filter(Q(author=followee) | Q(author=request_user)).order_by('-created_at')
    if following_tags:
        following_tag_list = []
        for following_tag in following_tags:
            following_tag_list.append(following_tag.tag.name)
        tag_post_list = []
        for tag in following_tag_list:
            tag_post = Posts.objects.filter(tag=tag)
            tag_post_list = list(chain(tag_post_list, tag_post))
    if following_tags and followees:
        timeline_post_list = list(chain(friend_and_my_posts, tag_post_list))
    elif following_tags and (not followees):
        my_posts = Posts.objects.filter(author=request_user)
        timeline_post_list = list(chain(my_posts, tag_post_list))
    else:
        timeline_post_list = list(friend_and_my_posts)
    # queryset.sort(key=attrgetter('created_at'), reverse=True)
    # timeline_post_list.sort(key=lambda x: x.created_at, reverse=True)

    return timeline_post_list


def find_reccomended_users(request_user, followee_friendships, follower_friendships):
    """
    「知り合いかも」にフォローしてる、
    もしくはフォローされてる友達のフォローしてる人を
    おすすめとして表示させるための処理
    return: list
    """

    alrealdy_followees = list(request_user.followees.all())
    reccomended_users = []
    for relation in followee_friendships:
        followee_friend_followees = relation.followee.followees.all()
        followee_friend_followers = relation.followee.followers.all()
        for followee_friend_followee in followee_friend_followees:
            if followee_friend_followee in reccomended_users:
                continue
            elif request_user == followee_friend_followee:
                continue
            elif followee_friend_followee in alrealdy_followees:
                continue
            reccomended_users.append(followee_friend_followee)
        for followee_friend_follower in followee_friend_followers:
            if followee_friend_follower in reccomended_users:
                continue
            elif request_user == followee_friend_follower:
                continue
            elif followee_friend_follower in alrealdy_followees:
                continue
            reccomended_users.append(followee_friend_follower)
    for relation in follower_friendships:
        follower_friend_followees = relation.follower.followees.all()
        follower_friend_followers = relation.follower.followers.all()
        for follower_friend_followee in follower_friend_followees:
            if follower_friend_followee in reccomended_users:
                continue
            elif request_user == follower_friend_followee:
                continue
            elif follower_friend_followee in alrealdy_followees:
                continue
            reccomended_users.append(follower_friend_followee)
        for follower_friend_follower in follower_friend_followers:
            if follower_friend_follower in reccomended_users:
                continue
            elif request_user == follower_friend_follower:
                continue
            elif follower_friend_follower in alrealdy_followees:
                continue
            reccomended_users.append(follower_friend_follower)

    return reccomended_users


class PostView(LoginRequiredMixin, CreateView):
    template_name = 'post.html'
    form_class = PostForm
    success_url = reverse_lazy('instagram:home')

    def form_valid(self, form):
        post = form.save(commit=False)
        author = self.request.user
        post.author = author
        tags = post.tag
        post.save()
        if tags:
            tags_list = tags.split('#')
            tags_list.pop(0)
            for tag in tags_list:
                tag = '#' + tag
                tag_exist = Tag.objects.filter(name=tag)
                if not tag_exist:
                    Tag.objects.create(name=tag)
                tag = Tag.objects.get(name=tag)
                PostTagRelation.objects.get_or_create(post=post, tag=tag)
        return super(PostView, self).form_valid(form)


class DeletePostView(LoginRequiredMixin, DeleteView):
    template_name = 'posts_confirm_delete.html'
    model = Posts
    success_url = reverse_lazy('instagram:home')


class UpdatePostView(LoginRequiredMixin, UpdateView):
    template_name = 'edit_post.html'
    model = Posts
    form_class = UpdatePostForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = Posts.objects.get(pk=self.kwargs['pk'])
        context['image'] = post.image
        return context

    def form_valid(self, form):
        post = form.save(commit=False)
        tags = post.tag
        if tags:
            tags_list = tags.split('#')
            tags_list.pop(0)
            for tag in tags_list:
                tag = '#' + tag
                tag_exist = Tag.objects.filter(name=tag)
                if not tag_exist:
                    Tag.objects.create(name=tag)
                tag = Tag.objects.get(name=tag)
                PostTagRelation.objects.get_or_create(post=post, tag=tag)
        return super(UpdatePostView, self).form_valid(form)

    def get_success_url(self):
        return reverse('instagram:post_detail', kwargs={'pk': self.kwargs['pk']})



class UserProfileView(LoginRequiredMixin, ListView):
    template_name = 'user_profile.html'
    queryset = Posts
    context_object_name = 'posts'
    paginate_by = 15

    def get_queryset(self):
        user = User.objects.get(pk=self.kwargs['pk'])
        queryset = Posts.objects.filter(author=user).order_by('-created_at')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(pk=self.kwargs['pk'])
        context['user_profile'] = user
        context['request_user'] = self.request.user
        followee_count = FriendShip.objects.filter(follower__username=user.username).count()
        tag_follow_count = FollowTag.objects.filter(user=user).count()
        context['followee'] = followee_count + tag_follow_count
        context['follower'] = FriendShip.objects.filter(followee__username=user.username).count()
        context['post_count'] = Posts.objects.filter(author=user).count()
        if user.username is not context['request_user']:
            result = FriendShip.objects.filter(follower__username=context['request_user'].username).filter(followee__username=user.username)
            context['connected'] = True if result else False
        return context


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'edit_user_profile.html'
    model = User
    form_class = UserProfileUpdateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_user = User.objects.get(pk=self.kwargs['pk'])
        context['user_image'] = request_user.user_image
        return context
    
    def get_success_url(self):
        return reverse('instagram:user_profile', kwargs={'pk': self.kwargs['pk']})


@login_required
def like_post(request, *args, **kwargs):
    """
    いいね機能のための関数
    """
    post = Posts.objects.get(pk=kwargs['pk'])
    is_like = PostLikes.objects.filter(user=request.user).filter(post=post).count()
    if is_like > 0:
        like = PostLikes.objects.get(user=request.user, post__id=kwargs['pk'])
        like.delete()
        post.like_count -= 1
        post.save()
        return redirect(reverse_lazy('instagram:home'))
    post.like_count += 1
    post.save()
    post_like = PostLikes()
    post_like.user = request.user
    post_like.post = post
    post_like.save()
    return redirect(reverse_lazy('instagram:home'))


@login_required
def save_post(request, *args, **kwargs):
    """
    save機能のための関数
    """
    post = Posts.objects.get(pk=kwargs['pk'])
    is_saved = PostSave.objects.filter(user=request.user).filter(post=post).count()
    if is_saved> 0:
        save = PostSave.objects.get(user=request.user, post__id=kwargs['pk'])
        save.delete()
        return redirect(reverse_lazy('instagram:home'))
    post_save = PostSave()
    post_save.user = request.user
    post_save.post = post
    post_save.save()
    return redirect(reverse_lazy('instagram:home'))


class CommentToPostView(LoginRequiredMixin, CreateView):
    template_name = 'comment_to_post.html'
    form_class = CommentToPostForm

    def form_valid(self, form):
        author = self.request.user
        post = Posts.objects.get(pk=self.kwargs['pk'])
        post.comment_count += 1
        post.save()
        form.instance.author = author
        form.instance.post = post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('instagram:post_detail', kwargs={'pk':self.kwargs['pk']})


@csrf_protect
def comment_to_comment(request, pk):
    """
    コメントに対してコメントするための関数
    フォームの先頭の文字が@だったら、この関数が呼ばれる
    """
    print('here4')
    form = CommentToCommentForm(request.POST or None)
    print(form)
    text = request.POST.get('text')
    if form.is_valid():
        print('here5')
        comment_text = text.lstrip('@')
        author = request.user
        to_comment_author = comment_text.split()[0]
        post = Posts.objects.get(pk=pk)
        to_comment_author = User.objects.get(username=to_comment_author)
        to_comment = CommentToPost.objects.filter(author=to_comment_author, post=post)
        to_comment.comment_count += 1
        to_comment.save()
        CommentToComment.objects.create(
            text=text,
            author=author,
            to_comment=to_comment,
        )
    return redirect('instagram:post_detail', pk=pk)


class DeleteCommentView(LoginRequiredMixin, DeleteView):
    template_name = 'comment_confirm_delete.html'
    model = CommentToPost
    success_url = reverse_lazy('instagram:home')


@csrf_protect
def comment_from_post_list(request, pk):
    """
    投稿一覧画面から直接コメントをするための関数
    """
    comment_text = request.POST['text']
    if comment_text.startswith('@'):
        # return redirect('instagram:comment_to_comment', pk=pk)
        form = CommentToCommentForm(request.POST or None)
        if form.is_valid():
            author = request.user
            text = comment_text.lstrip('@')
            to_comment_author = text.split()[0]
            post = Posts.objects.get(pk=pk)
            to_comment_author = User.objects.filter(username=to_comment_author).first()
            to_comment = CommentToPost.objects.filter(author=to_comment_author, post=post).first()
            to_comment.comment_count += 1
            to_comment.save()
            CommentToComment.objects.create(
                text=comment_text,
                author=author,
                to_comment=to_comment,
            )
    else:
        form = CommentFromPostListForm(request.POST or None)
        if form.is_valid():
            text = request.POST['text']
            author = request.user
            post = Posts.objects.get(pk=pk)
            post.comment_count += 1
            post.save()
            CommentToPost.objects.create(
                text=text,
                author=author,
                post=post,
            )
            print('here3')
    return redirect('instagram:post_detail', pk=pk)


class PostDetailView(LoginRequiredMixin, ListView):
    template_name = 'post_detail.html'
    queryset = Posts

    def get_queryset(self):
        post_author = Posts.objects.get(pk=self.kwargs['pk']).author
        queryset = Posts.objects.filter(author=post_author).order_by('-created_at')[:6]
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = Posts.objects.get(pk=self.kwargs['pk'])
        user = self.request.user
        context['request_user'] = user
        context['comments'] = CommentToPost.objects.filter(post=self.kwargs['pk'])
        context['comment_from_post_list_form'] = CommentFromPostListForm()
        return context


@login_required
def follow_view(request, *args, **kwargs):
    """
    ユーザーをフォローするための関数
    """
    try:
        follower = User.objects.get(pk=request.user.pk)
        followee = User.objects.get(pk=kwargs['pk'])
    except User.DoesNotExist:
        messages.warning(request, 'ユーザーが存在しません')
        return redirect(reverse_lazy('instagram:home'))
    
    if follower == followee:
        messages.warning(request, '自分自身はフォローできません')
    else:
        _, created = FriendShip.objects.get_or_create(followee=followee, follower=follower)
        if created:
            messages.warning(request, 'フォローしました')
        else:
            messages.warning(request, 'あなたは既にフォローしています')
    # return redirect(reverse_lazy('instagram:user_profile', kwargs={'pk':followee.pk}))
    #前の画面に遷移
    return redirect(request.META['HTTP_REFERER'])


@login_required
def unfollow_view(request, *args, **kwargs):
    """
    既にフォローしているユーザーのフォローを解除するための関数
    """
    try:
        follower = User.objects.get(pk=request.user.pk)
        followee = User.objects.get(pk=kwargs['pk'])
        if follower == followee:
            messages.warning('自分自身のフォローは外せません')
        else:
            unfollow = FriendShip.objects.get(followee=followee, follower=follower)
            unfollow.delete()
            messages.success(request, 'フォローを外しました')
    except User.DoesNotExist:
        messages.warning(request, 'ユーザーが存在しません')
        return redirect(reverse_lazy('instagram:home'))
    except FriendShip.DoesNotExist:
        messages.warning(request, 'フォローしてません')
    # return redirect(reverse_lazy('instagram:user_profile', kwargs={'pk':followee.pk}))
    #前の画面に遷移
    return redirect(request.META['HTTP_REFERER'])


class FolloweeListView(LoginRequiredMixin, ListView):
    template_name = 'followee_list.html'
    queryset = User
    paginate_by = 16

    def get_queryset(self):
        user = User.objects.get(pk=self.kwargs['pk'])
        queryset = User.objects.filter(followers=user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(pk=self.kwargs['pk'])
        request_user = self.request.user
        context['tag_following'] = FollowTag.objects.filter(user=request_user)
        context['request_user'] = request_user
        context['user_profile'] = user
        followee_count = FriendShip.objects.filter(follower__username=user.username).count()
        tag_follow_count = FollowTag.objects.filter(user=user).count()
        context['followee'] = followee_count + tag_follow_count
        context['follower'] = FriendShip.objects.filter(followee__username=user.username).count()
        return context


class FollowerListView(LoginRequiredMixin, ListView):
    template_name = 'follower_list.html'
    queryset = User
    paginate_by = 16

    def get_queryset(self):
        user = User.objects.get(pk=self.kwargs['pk'])
        queryset = User.objects.filter(followees=user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(pk=self.kwargs['pk'])
        context['request_user'] = self.request.user
        context['user_profile'] = user
        followee_count = FriendShip.objects.filter(follower__username=user.username).count()
        tag_follow_count = FollowTag.objects.filter(user=user).count()
        context['followee'] = followee_count + tag_follow_count
        context['follower'] = FriendShip.objects.filter(followee__username=user.username).count()
        return context


class MessagesView(LoginRequiredMixin, ListView):
    template_name = 'messages.html'
    queryset = Message
    paginate_by=20

    def get_queryset(self):
        request_user = self.request.user
        queryset = Message.objects.filter(Q(to_user=self.kwargs['pk']) | Q(from_user=self.kwargs['pk']))\
                    .filter(Q(from_user=request_user.pk) | Q(to_user=request_user)).order_by('created_at')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_user = self.request.user
        context['request_user'] = request_user
        context['to_user'] = User.objects.get(pk=self.kwargs['pk'])
        context['message_form'] = MessageForm()
        #もしDMが来てるもしくは、リクエストユーザーが誰かにDMを送っている場合はその人を優先的にリストアップする処理
        context['reccomended_users'] = find_message_address(request_user)
        #メッセージを送る相手を検索する処理
        query = self.request.GET.get('query')
        if query:
            context['reccomended_users'] = User.objects.filter(followers=request_user).filter(Q(username__icontains=query) | Q(name__icontains=query))[:10]
        return context
    #メッセージを送る処理
    def post(self, request, *args, **kwargs):
        message_form = MessageForm(request.POST or None)
        if message_form.is_valid():
            to_user = User.objects.get(pk=self.kwargs['pk'])
            from_user = self.request.user
            message = Message(to_user=to_user, from_user=from_user, **message_form.cleaned_data)
            message.save()
            return redirect('instagram:messages', pk=to_user.pk)
        return super(MessagesView, self).post(request, *args, **kwargs)

#メッセージ画面（送信先未定）
class MessageListView(LoginRequiredMixin, ListView):
    template_name = 'message_list.html'
    queryset = User

    def get_queryset(self):
        request_user = self.request.user
        queryset = User.objects.filter(followers=request_user)[:10]
        #もしDMが来てるもしくは、リクエストユーザーが誰かにDMを送っている場合はその人を優先的にリストアップする処理
        queryset = find_message_address(request_user)
        #メッセージを送る相手を検索する処理
        query = self.request.GET.get('query')
        if query:
            queryset = User.objects.filter(followers=request_user).filter(Q(username__icontains=query) | Q(name__icontains=query))[:10]
        return queryset


def find_message_address(request_user):
    """
    メッセージ画面で送信先のユーザー一覧を生成する関数
    return: list or QuerySet
    """
    messages = Message.objects.filter(Q(to_user=request_user) | Q(from_user=request_user))
    if messages:
        to_user_list = []
        #誰かと既にメッセージをしている場合はその相手をリストアップする
        for message in messages:
            if message.from_user in to_user_list:
                continue
            elif message.to_user == message.from_user:
                continue
            else:
                from_user = message.from_user
                to_user = message.to_user
                to_user_list.append(from_user)
                to_user_list.append(to_user)
        following_users = User.objects.filter(followers=request_user)[:10]
        following_user_list = []
        for user in following_users:
            if user in to_user_list:
                continue
            else:
                following_user_list.append(user)
        to_user_list = list(chain(to_user_list, following_user_list))
        #送信先一覧に自分がいるバグを避けるため
        if request_user in to_user_list:
            while request_user in to_user_list:
                to_user_list.remove(request_user)
    else:
        to_user_list = User.objects.filter(followers=request_user)[:10]

    return to_user_list


class TagPostListView(LoginRequiredMixin, ListView):
    template_name = 'tag_post_list.html'
    queryset = Posts
    paginate_by = 27

    def get_queryset(self):
        tag = self.kwargs['tag']
        post_tag_relation = PostTagRelation.objects.filter(tag__name=tag).order_by('-post__created_at')
        post_list = []
        for post_tag in post_tag_relation:
            post_list.append(post_tag.post)
        queryset = post_list
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag = self.kwargs['tag']
        context['tag'] = Tag.objects.get(name=tag)
        context['num_of_posts'] = PostTagRelation.objects.filter(tag__name=tag).count()
        request_user = self.request.user
        context['request_user'] = request_user
        tag = self.kwargs['tag']
        post_tag_relation_first = PostTagRelation.objects.filter(tag__name=tag)
        if post_tag_relation_first:
            context['first_post'] = post_tag_relation_first.first().post
        result = FollowTag.objects.filter(user__username=request_user.username).filter(tag__name=tag)
        context['connected'] = True if result else False
        return context


class SearchFriendsView(LoginRequiredMixin, ListView):
    template_name = 'search_friends.html'
    queryset = User
    paginate_by = 16

    def get_queryset(self):
        user = self.request.user
        search_friends = self.request.GET.get('search_friends')
        if search_friends:
            #ここでは既にフォローもしくはフォローされているユーザー、知り合いかもしれないユーザーを優先的に上位にリストアップするための処理
            #distinctによって検索結果の重複を避けている
            friends = User.objects.filter(Q(followees=user) | Q(followers=user))\
                .filter(Q(username__icontains=search_friends) | Q(name__icontains=search_friends)).distinct()
            followee_friendships = FriendShip.objects.filter(follower__username=user)
            follower_friendships = FriendShip.objects.filter(followee__username=user)
            reccomended_users = find_reccomended_users(user, followee_friendships, follower_friendships)
            acquaintance_list = []
            friends_list = []
            for friend in friends:
                friends_list.append(friend.username)
            for reccomended_user in reccomended_users:
                if reccomended_user.username in friends_list:
                    continue
                else:
                    if search_friends in reccomended_user.username:
                        acquaintance_list.append(reccomended_user)
                    else:
                        continue
            other_users = User.objects.filter(Q(username__icontains=search_friends) | Q(name__icontains=search_friends))
            other_users_list = []
            for other_user in other_users:
                if (other_user in acquaintance_list) or (other_user in friends):
                    continue
                else:
                    other_users_list.append(other_user)
            queryset = list(chain(friends, acquaintance_list, other_users_list))

        #以下は友達を探すのユーザーリストのデフォルトとして、知り合いの知り合いまでリストアップする処理
        else:
            followee_friendships = FriendShip.objects.filter(follower__username=user)
            follower_friendships = FriendShip.objects.filter(followee__username=user)
            queryset = find_reccomended_users(user, followee_friendships, follower_friendships)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['request_user'] = user
        followee_count = FriendShip.objects.filter(follower__username=user.username).count()
        tag_follow_count = FollowTag.objects.filter(user=user).count()
        context['followee'] = followee_count + tag_follow_count
        context['follower'] = FriendShip.objects.filter(followee=user).count()
        return context


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'settings.html'


class ReccomendedPostsView(LoginRequiredMixin, ListView):
    template_name = 'reccomended_posts.html'
    queryset = Posts
    paginate_by = 27

    def get_queryset(self):
        """
        ログインユーザーへのおすすめの投稿を
        リストアップするメソッド
        """
        request_user = self.request.user
        #ログインユーザーがいいねした投稿のタグに基づいて、おすすめの投稿を取得
        liked_posts = PostLikes.objects.filter(user=request_user)
        liked_post_tag_list = []
        for liked_post in liked_posts.all():
            liked_post_tag = liked_post.post.tag
            if liked_post_tag in liked_post_tag_list:
                continue
            else:
                liked_post_tag_list.append(liked_post_tag)
        reccomended_posts_by_tag = []
        for liked_post_tag in liked_post_tag_list:
            reccomended_posts = Posts.objects.filter(tag=liked_post_tag)
            for reccomended_post in reccomended_posts:
                if reccomended_post in reccomended_posts_by_tag:
                    continue
                else:
                    reccomended_posts_by_tag.append(reccomended_post)
        #フォローしているユーザーの投稿を取得
        followees_posts = []
        for followee in request_user.followees.all():
            followee_posts = Posts.objects.filter(author=followee)
            for followee_post in followee_posts:
                if followee_post in reccomended_posts_by_tag:
                    continue
                else:
                    followees_posts.extend(followee_posts)
        #フォローしているユーザーの投稿をすべて返すのは多すぎるので、いいねした
        #投稿の7分の1の数の投稿を返す
        followees_posts_num = math.floor(len(reccomended_posts_by_tag)/7)
        if len(followees_posts) < followees_posts_num:
            followees_posts_num = len(followees_posts)
        followees_posts = random.sample(followees_posts, followees_posts_num)
        reccomended_posts = list(chain(reccomended_posts_by_tag, followees_posts))
        random.shuffle(reccomended_posts)
        if not (liked_posts and request_user.followees):
            reccomended_posts = Posts.objects.all()[:40]
        queryset = reccomended_posts
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_user'] = self.request.user
        return context


class SeeAllReccomendedUsersView(LoginRequiredMixin, ListView):
    template_name = 'see_all_reccomended_users.html'
    queryset = User
    paginate_by = 16

    def get_queryset(self):
        request_user = self.request.user
        followee_friendships = FriendShip.objects.filter(follower__username=request_user)
        follower_friendships = FriendShip.objects.filter(followee__username=request_user)
        queryset = find_reccomended_users(request_user, followee_friendships, follower_friendships)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_user = self.request.user
        context['request_user'] = request_user
        followee = User.objects.filter(followers=request_user).count()
        follower = User.objects.filter(followees=request_user).count()
        context['followee'] = followee
        context['follower'] = follower
        return context


class LikedPostListView(LoginRequiredMixin, ListView):
    template_name = 'liked_post_list.html'
    queryset = Posts
    paginate_by = 27

    def get_queryset(self):
        request_user = self.request.user
        post_likes = PostLikes.objects.filter(user=request_user).order_by('-created_at')
        liked_post_list = []
        for post_like in post_likes:
            liked_post_list.append(post_like.post)
        queryset = liked_post_list
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_user = self.request.user
        context['request_user'] = request_user
        return context


class LikedPostUserView(LoginRequiredMixin, ListView):
    template_name = 'liked_post_user.html'
    queryset = User
    paginate_by = 16

    def get_queryset(self):
        post = Posts.objects.get(pk=self.kwargs['pk'])
        post_likes = PostLikes.objects.filter(post=post)
        queryset = []
        for post_like in post_likes:
            queryset.append(post_like.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_user = self.request.user
        context['request_user'] = request_user
        followee = User.objects.filter(followers=request_user).count()
        follower = User.objects.filter(followees=request_user).count()
        context['followee'] = followee
        context['follower'] = follower
        return context


class SavedPostListView(LoginRequiredMixin, ListView):
    template_name = 'saved_post_list.html'
    queryset = Posts
    paginate_by = 15

    def get_queryset(self):
        user = User.objects.get(pk=self.kwargs['pk'])
        post_save = PostSave.objects.filter(user=user)
        saved_post_list = []
        for post in post_save:
            saved_post_list.append(post.post)
        queryset = saved_post_list
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(pk=self.kwargs['pk'])
        context['user_profile'] = User.objects.get(pk=user.pk)
        context['request_user'] = self.request.user
        followee_count = FriendShip.objects.filter(follower__username=user.username).count()
        tag_follow_count = FollowTag.objects.filter(user=user).count()
        context['followee'] = followee_count + tag_follow_count
        context['follower'] = FriendShip.objects.filter(followee__username=user.username).count()
        return context


class UserFollowerFriendListView(LoginRequiredMixin, ListView):
    template_name = 'user_follower_friend_list.html'
    queryset = User
    paginate_by = 16

    def get_queryset(self):
        request_user = self.request.user
        request_user_followees = request_user.followees.all()
        profile_user = User.objects.get(pk=self.kwargs['pk'])
        profile_user_follwers = profile_user.followers.all()
        user_follower_friend_list = []
        if request_user_followees and profile_user_follwers:
            for requset_user_followee in request_user_followees:
                if requset_user_followee in profile_user_follwers:
                    user_follower_friend_list.append(requset_user_followee)
                else:
                    continue
            queryset = user_follower_friend_list
        else:
            queryset = None
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_user = self.request.user
        context['request_user'] = request_user
        followee = User.objects.filter(followers=request_user).count()
        follower = User.objects.filter(followees=request_user).count()
        context['followee'] = followee
        context['follower'] = follower
        return context


@login_required
def follow_tag_view(request, *args, **kwargs):
    """
    タグをフォローするための関数
    """
    try:
        user = User.objects.get(pk=request.user.pk)
        tag = Tag.objects.get(pk=kwargs['pk'])
    except Tag.DoesNotExist:
        messages.warning(request, 'タグが存在しません')
        return redirect(reverse_lazy('instagram:home'))

    _, created = FollowTag.objects.get_or_create(user=user, tag=tag)
    if created:
        messages.warning(request, 'フォローしました')
    else:
        messages.warning(request, 'あなたは既にフォローしています')
    #前の画面に遷移
    return redirect(request.META['HTTP_REFERER'])

    
@login_required
def unfollow_tag_view(request, *args, **kwargs):
    """
    既にフォローしているタグのフォローを解除するための関数
    """
    try:
        user = User.objects.get(pk=request.user.pk)
        tag = Tag.objects.get(pk=kwargs['pk'])
        unfollow = FollowTag.objects.get(user=user, tag=tag)
        unfollow.delete()
        messages.success(request, 'フォローを外しました')
    except Tag.DoesNotExist:
        messages.warning(request, 'ユーザーが存在しません')
        return redirect(reverse_lazy('instagram:home'))
    except FollowTag.DoesNotExist:
        messages.warning(request, 'フォローしてません')
    #前の画面に遷移
    return redirect(request.META['HTTP_REFERER'])


class FollowingHashtagListView(LoginRequiredMixin, ListView):
    template_name = 'following_hashtag_list.html'
    queryset = Tag
    paginate_by = 16

    def get_queryset(self):
        user = User.objects.get(pk=self.kwargs['pk'])
        following_tags = FollowTag.objects.filter(user=user)
        tag_list = []
        for following_tag in following_tags:
            tag_list.append(following_tag.tag)
        queryset = tag_list
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        requset_user = self.request.user
        user = User.objects.get(pk=self.kwargs['pk'])
        context['request_user'] = requset_user
        context['user_profile'] = user
        followee_count = FriendShip.objects.filter(follower__username=user.username).count()
        tag_follow_count = FollowTag.objects.filter(user=user).count()
        context['followee'] = followee_count + tag_follow_count
        context['follower'] = FriendShip.objects.filter(followee__username=user.username).count()
        return context