from typing import Text
from django.core.checks import messages
from django.db.models import query
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
from .models import CommentToPost, FriendShip, PostLikes, Posts
from .forms import PostForm, UserProfileUpdateForm, CommentToPostForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages


class HomeView(LoginRequiredMixin, ListView):
    template_name = 'home.html'
    queryset = Posts

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.objects.order_by('-post_date')
        query = self.request.GET.get('query')
        if query:
            queryset = queryset.filter(Q(text__icontains=query) | Q(author__username__icontains=query) | Q(tag__icontains=query))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        context['followee'] = FriendShip.objects.filter(follower__username=user).count()
        context['follower'] = FriendShip.objects.filter(followee__username=user).count()
        return context


class PostView(LoginRequiredMixin, CreateView):
    template_name = 'post.html'
    form_class = PostForm
    success_url = reverse_lazy('instagram:home')

    def form_valid(self, form):
        author = self.request.user
        form.instance.author = author
        return super(PostView, self).form_valid(form)


class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'user_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(pk=self.kwargs['pk'])
        context['posts'] = Posts.objects.filter(author=user)
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
        form.instance.author = author
        form.instance.post = post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('instagram:post_detail', kwargs={'pk':self.kwargs['pk']})


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

    def get_queryset(self):
        queryset = super().get_queryset()
        user = User.objects.get(pk=self.kwargs['pk'])
        queryset = User.objects.filter(followers=user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_user'] = self.request.user
        return context


class FollowerListView(LoginRequiredMixin, ListView):
    template_name = 'follower_list.html'
    queryset = User

    def get_queryset(self):
        queryset = super().get_queryset()
        user = User.objects.get(pk=self.kwargs['pk'])
        queryset = User.objects.filter(followees=user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_user'] = self.request.user
        return context