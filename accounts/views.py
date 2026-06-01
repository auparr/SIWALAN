from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages

def login_view(request):
    if request.user.is_authenticated:
        return redirect('schedules:dashboard_dosen')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                return redirect('schedules:dashboard_dosen')
        else:
            messages.error(request, "Username atau Password salah.")
            
    form = AuthenticationForm()

    context = {'form': form}
    return render(request, 'accounts/login.html', context)

def logout_view(request):
    logout(request)
    messages.success(request, "Anda telah berhasil logout.")
    return redirect('login') 