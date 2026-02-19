from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserUpdateForm, ProfileUpdateForm

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        # Ensure profile exists before accessing it
        if not hasattr(request.user, 'profile'):
            from .models import Profile
            Profile.objects.create(user=request.user)
            
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Jūsų profilis sėkmingai atnaujintas!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        # Ensure profile exists
        if not hasattr(request.user, 'profile'):
            from .models import Profile
            Profile.objects.create(user=request.user)
            
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'users/profile.html', context)
