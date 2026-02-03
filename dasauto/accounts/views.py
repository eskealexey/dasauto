# Create your views here.

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from .forms import RegisterForm


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # Создаём пользователя — пароль автоматически хэшируется
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            # Автоматический вход после регистрации (опционально)
            login(request, user)
            messages.success(request, 'Вы успешно зарегистрированы!')
            return redirect('home')  # Замените 'home' на нужный URL
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form})
