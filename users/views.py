from django.shortcuts import render, redirect
from .models import User
from django.contrib.auth import login, authenticate
from django.views.generic import CreateView, View
from .forms import LoginForm, CreateUserForm
from django.contrib.auth import logout
from django.urls import reverse


class CreateUser(CreateView):

    def post(self, request, *args, **kwargs):
        form = CreateUserForm(data=request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('users:login')
        return render(request, 'signup.html', {'form':form})
    
    def get(self, request, *args, **kwargs):
        form = CreateUserForm(request.POST)
        return render(request, 'signup.html', {'form':form})


class UserLogin(View):
    
    def post(self, request, *args, **kwargs):
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            user = User.objects.get(username=username)
            login(request, user)
            return redirect('instagram:home')
        return render(request, 'login.html', {'form':form})

    def get(self, request, *args, **kwargs):
        form = LoginForm(request.POST)
        return render(request, 'login.html', {'form':form})


def user_logout(request):
    logout(request)
    return redirect('instagram:home')