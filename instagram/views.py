from django.http import request
from users.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.urls.base import reverse
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Posts, UserProfile
from .forms import PostForm


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


class UserProfileView(ListView):
    template_name = 'user_profile.html'
    queryset = Posts
    
    def get_queryset(self):
        queryset = super().get_queryset()
        author = User.objects.get(pk=self.kwargs['pk'])
        queryset = Posts.objects.filter(author=author)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = UserProfile.objects.filter(user=self.kwargs['pk'])
        context['request_user'] = self.request.user
        return context