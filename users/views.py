from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from .forms import UserUpdateForm, ProfileUpdateForm, CustomPasswordChangeForm

@login_required
def profile(request):
    # Ensure profile exists
    if not hasattr(request.user, 'profile'):
        from .models import Profile
        Profile.objects.create(user=request.user)

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        # Check if user is trying to change password
        old_password = request.POST.get('old_password', '')
        new_password1 = request.POST.get('new_password1', '')
        new_password2 = request.POST.get('new_password2', '')
        changing_password = any([old_password, new_password1, new_password2])

        if changing_password:
            pw_form = CustomPasswordChangeForm(request.user, request.POST)
        else:
            pw_form = CustomPasswordChangeForm(request.user)

        if u_form.is_valid() and p_form.is_valid():
            if changing_password:
                if pw_form.is_valid():
                    u_form.save()
                    p_form.save()
                    user = pw_form.save()
                    update_session_auth_hash(request, user)
                    messages.success(request, 'Profilis ir slaptažodis sėkmingai atnaujinti!')
                    return redirect('profile')
                # If password form is invalid, still show errors
            else:
                u_form.save()
                p_form.save()
                messages.success(request, 'Profilis sėkmingai atnaujintas!')
                return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
        pw_form = CustomPasswordChangeForm(request.user)

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'pw_form': pw_form,
    }
    return render(request, 'users/profile.html', context)
