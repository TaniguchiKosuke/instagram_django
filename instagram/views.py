import random
from django import contrib
from django.core.checks import messages
from django.db.models import query
from django.forms.utils import to_current_timezone
from django.http import request
from django.views.generic.base import TemplateView
from users.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.urls.base import reverse, translate_url
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import CommentToPost, FriendShip, Message, PostLikes, Posts, Tag
from .forms import CommentFromPostListForm, MessageForm, PostForm, UserProfileUpdateForm, CommentToPostForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect


class HomeView(LoginRequiredMixin, ListView):
    template_name = 'home.html'
    queryset = Posts
    paginate_by = 8

    def get_queryset(self):
        queryset = super().get_queryset()
        #ユーザーが誰かフォローしている場合はその人の投稿を優先的に表示
        request_user = self.request.user
        query = self.request.GET.get('query')
        if query:
            #投稿を検索する処理
            if not query.startswith('#'):
                queryset = Posts.objects.filter(Q(text__icontains=query) | Q(author__username__icontains=query) | Q(tag__icontains=query))
            elif query.startswith('#'):
                queryset = Tag.objects.filter(Q(name__icontains=query))
        elif request_user.followees.all():
            for followee in request_user.followees.all():
                queryset = Posts.objects.filter(Q(author=followee) | Q(author=request_user)).order_by('-created_at')
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
        alrealdy_followees = list(user.followees.all())
        reccomended_users = []
        for relation in followee_friendships:
            followee_friend_followees = relation.followee.followees.all()
            followee_friend_followers = relation.followee.followers.all()
            for followee_friend_followee in followee_friend_followees:
                if followee_friend_followee in reccomended_users:
                    continue
                elif user == followee_friend_followee:
                    continue
                elif followee_friend_followee in alrealdy_followees:
                    continue
                reccomended_users.append(followee_friend_followee)
            for followee_friend_follower in followee_friend_followers:
                if followee_friend_follower in reccomended_users:
                    continue
                elif user == followee_friend_follower:
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
                elif user == follower_friend_followee:
                    continue
                elif follower_friend_followee in alrealdy_followees:
                    continue
                reccomended_users.append(follower_friend_followee)
            for follower_friend_follower in follower_friend_followers:
                if follower_friend_follower in reccomended_users:
                    continue
                elif user == follower_friend_follower:
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
        context['reccomended_users'] = reccomended_users
        return context


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
                print('そんなタグは存在しません')
                Tag.objects.create(name=tag)
        return super(PostView, self).form_valid(form)


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
    return redirect(reverse_lazy('instagram:user_profile', kwargs={'pk':followee.pk}))


@login_required
def unfollow_view(request, *args, **kwargs):
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
    return redirect(reverse_lazy('instagram:user_profile', kwargs={'pk':followee.pk}))


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
        #もしDMが来てるもしくは、リクエストユーザーが誰かにDMをオッくている場合はその人を優先的にリストアップする処理
        messages = Message.objects.filter(Q(to_user=request_user) | Q(from_user=request_user))
        if messages:
            from_user_list = []
            for message in messages:
                if message.from_user in from_user_list:
                    break
                else:
                    from_user = message.from_user
                    from_user_list.append(from_user)
            context['reccomended_users'] = from_user_list
        else:
            context['reccomended_users'] = User.objects.filter(followers=request_user)[:10]
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
        messages = Message.objects.filter(Q(to_user=request_user) | Q(from_user=request_user))
        if messages:
            from_user_list = []
            for message in messages:
                if message.from_user in from_user_list:
                    break
                else:
                    from_user = message.from_user
                    from_user_list.append(from_user)
            queryset = from_user_list
        else:
            queryset = User.objects.filter(followers=request_user)[:10]
        #メッセージを送る相手を検索する処理
        query = self.request.GET.get('query')
        if query:
            queryset = User.objects.filter(followers=request_user).filter(Q(username__icontains=query) | Q(name__icontains=query))[:10]
        return queryset


class TagPostListView(LoginRequiredMixin, ListView):
    template_name = 'tag_post_list.html'
    queryset = Posts
    paginate_by = 15

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
        return context


class SearchFriendsView(LoginRequiredMixin, ListView):
    template_name = 'search_friends.html'
    queryset = User
    paginate_by = 16

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        queryset = User.objects.filter(followees=user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['request_user'] = user
        context['followee'] = FriendShip.objects.filter(follower=user).count()
        context['follower'] = FriendShip.objects.filter(followee=user).count()
        search_friends = self.request.GET.get('search_friends')
        if search_friends:
            context['object_list'] = User.objects.filter(Q(username__icontains=search_friends) | Q(name__icontains=search_friends))
        return context