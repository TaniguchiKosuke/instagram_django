import math
import random
from django import contrib
from django.core.checks import messages
from django.db.models import fields, query
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
from .models import CommentToPost, FriendShip, Message, PostLikes, Posts, Tag
from .forms import CommentFromPostListForm, MessageForm, PostForm, UserProfileUpdateForm, CommentToPostForm, UpdatePostForm
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
        #ユーザーが誰かフォローしている場合はその人の投稿を優先的に表示
        request_user = self.request.user
        #投稿を検索する処理
        query = self.request.GET.get('query')
        if query:
            if not query.startswith('#'):
                queryset = Posts.objects.filter(Q(text__icontains=query) | Q(author__username__icontains=query) | Q(tag__icontains=query))
            elif query.startswith('#'):
                queryset = Tag.objects.filter(Q(name__icontains=query))
        #フォローしているユーザーがいる場合は、それらを考慮に入れておすすめの投稿を表示する
        elif request_user.followees.all():
            friend_posts_list = []
            for followee in request_user.followees.all():
                friend_posts = Posts.objects.filter(author=followee).order_by('-created_at')
                friend_posts_list = list(chain(friend_posts_list, friend_posts))
            my_posts = Posts.objects.filter(author=request_user).order_by('-created_at')
            all_posts_count = Posts.objects.all().count()
            if all_posts_count > 20:
                other_posts = Posts.objects.order_by('?')[:20]
            else:
                other_posts = Posts.objects.order_by('?')[:all_posts_count]
            other_posts_list = []
            for post in other_posts:
                if (not post in friend_posts_list) and (not post in my_posts):
                    other_posts_list.append(post)
                else:
                    continue
            queryset = list(chain(friend_posts_list, my_posts, other_posts_list))
            # queryset.sort(key=attrgetter('created_at'), reverse=True)
            queryset.sort(key=lambda x: x.created_at, reverse=True)
        else:
            queryset = Posts.objects.order_by('-created_at')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        followee_friendships = FriendShip.objects.filter(follower__username=user)
        follower_friendships = FriendShip.objects.filter(followee__username=user)
        context['followee'] = followee_friendships.count()
        context['follower'] = follower_friendships.count()
        context['comment_from_post_list_form'] = CommentFromPostListForm()
        query = self.request.GET.get('query')
        if query:
            context['query_exist'] = True
            if query.startswith('#'):
                context['tags'] = Tag.objects.filter(Q(name__icontains=query))

        #「知り合いかも」にフォローしてる、もしくはフォローされてる友達のフォローしてる人をおすすめとして表示させるための処理
        reccomended_users = find_reccomended_users(user, followee_friendships, follower_friendships)
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


def find_reccomended_users(request_user, followee_friendships, follower_friendships):
    """
    「知り合いかも」にフォローしてる、
    もしくはフォローされてる友達のフォローしてる人を
    おすすめとして表示させるための処理
    return: reccomended_users
    type: list
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
    #reccomended_usersはシャッフルしたい
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

    return reccomended_users


class PostView(LoginRequiredMixin, CreateView):
    template_name = 'post.html'
    form_class = PostForm
    success_url = reverse_lazy('instagram:home')

    def form_valid(self, form):
        author = self.request.user
        form.instance.author = author
        tag = form.instance.tag
        if tag:
            tag_exist = Tag.objects.filter(name=tag)
            if not tag_exist:
                Tag.objects.create(name=tag)
        return super(PostView, self).form_valid(form)


class DeletePostView(LoginRequiredMixin, DeleteView):
    template_name = 'posts_confirm_delete.html'
    model = Posts
    success_url = reverse_lazy('instagram:home')


class UpdatePostView(LoginRequiredMixin, UpdateView):
    template_name = 'edit_post.html'
    model = Posts
    form_class = UpdatePostForm

    def get_success_url(self):
        return reverse('instagram:post_detail', kwargs={'pk': self.kwargs['pk']})



class UserProfileView(LoginRequiredMixin, ListView):
    template_name = 'user_profile.html'
    queryset = Posts
    context_object_name = 'posts'
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset()
        user = User.objects.get(pk=self.kwargs['pk'])
        queryset = queryset.objects.filter(author=user).order_by('-created_at')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(pk=self.kwargs['pk'])
        context['user_profile'] = User.objects.get(pk=user.pk)
        context['request_user'] = self.request.user
        context['followee'] = FriendShip.objects.filter(follower__username=user.username).count()
        context['follower'] = FriendShip.objects.filter(followee__username=user.username).count()
        if user.username is not context['request_user']:
            result = FriendShip.objects.filter(follower__username=context['request_user'].username).filter(followee__username=user.username)
            context['connected'] = True if result else False
        return context


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'edit_user_profile.html'
    model = User
    form_class = UserProfileUpdateForm
    
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
def comment_from_post_list(request, pk):
    """
    投稿一覧画面から直接コメントをするための関数
    """
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
    return redirect(reverse_lazy('instagram:home'))


class PostDetailView(LoginRequiredMixin, DetailView):
    template_name = 'post_detail.html'
    model = Posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = CommentToPost.objects.filter(post=self.kwargs['pk'])
        context['request_user'] = self.request.user
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
        queryset = super().get_queryset()
        user = User.objects.get(pk=self.kwargs['pk'])
        queryset = User.objects.filter(followers=user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(pk=self.kwargs['pk'])
        context['request_user'] = self.request.user
        context['user_profile'] = user
        context['followee'] = FriendShip.objects.filter(follower__username=user.username).count()
        context['follower'] = FriendShip.objects.filter(followee__username=user.username).count()
        return context


class FollowerListView(LoginRequiredMixin, ListView):
    template_name = 'follower_list.html'
    queryset = User
    paginate_by = 16

    def get_queryset(self):
        queryset = super().get_queryset()
        user = User.objects.get(pk=self.kwargs['pk'])
        queryset = User.objects.filter(followees=user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(pk=self.kwargs['pk'])
        context['request_user'] = self.request.user
        context['user_profile'] = user
        context['followee'] = FriendShip.objects.filter(follower__username=user.username).count()
        context['follower'] = FriendShip.objects.filter(followee__username=user.username).count()
        return context


class MessagesView(LoginRequiredMixin, ListView):
    template_name = 'messages.html'
    queryset = Message
    paginate_by=20

    def get_queryset(self):
        queryset = super().get_queryset()
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
        queryset = super().get_queryset()
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
    return: to_user_list
    type: list or QuerySet
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
        queryset = super().get_queryset()
        tag = self.kwargs['tag']
        queryset = Posts.objects.filter(tag=tag).order_by('-like_count')
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag = self.kwargs['tag']
        context['tag'] = tag
        context['num_of_posts'] = Posts.objects.filter(tag=tag).count()
        context['request_user'] = self.request.user
        return context


class SearchFriendsView(LoginRequiredMixin, ListView):
    template_name = 'search_friends.html'
    queryset = User
    paginate_by = 16

    def get_queryset(self):
        queryset = super().get_queryset()
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
        context['followee'] = FriendShip.objects.filter(follower=user).count()
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
        queryset = super().get_queryset()
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
        queryset = reccomended_posts
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_user'] = self.request.user
        return context


class SeeAllReccomendedUsersView(LoginRequiredMixin, ListView):
    template_name = 'see_all_reccomended_users.html'
    queryset = User

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = User.objects.all()
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