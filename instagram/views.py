from django.db.models import query
from django.http import request
from django.views.generic.base import TemplateView
from users.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.urls.base import reverse
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import PostLikes, Posts
from .forms import PostForm, UserProfileUpdateForm
from django.contrib.auth.decorators import login_required


class HomeView(ListView):
    template_name = 'home.html'
    queryset = Posts

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.objects.order_by('-post_date')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class PostView(LoginRequiredMixin, CreateView):
    template_name = 'post.html'
    form_class = PostForm
    success_url = reverse_lazy('instagram:home')

    def form_valid(self, form):
        author = self.request.user
        form.instance.author = author
        return super(PostView, self).form_valid(form)


class UserProfileView(TemplateView):
    template_name = 'user_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = User.objects.get(pk=self.kwargs['pk'])
        context['posts'] = Posts.objects.filter(author=user)
        context['user_profile'] = User.objects.get(pk=user.pk)
        context['request_user'] = self.request.user
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
    pass