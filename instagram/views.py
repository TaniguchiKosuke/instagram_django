from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.urls.base import reverse
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Posts


class HomeView(LoginRequiredMixin, ListView):
    template_name = 'home.html'
    queryset = Posts.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context