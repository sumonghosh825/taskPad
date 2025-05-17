from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.hashers import check_password
from django.contrib import messages
import uuid
from django.views.decorators.csrf import csrf_exempt

from .models import Profile, Role, Users_to_Roles
from django.contrib.auth.decorators import login_required

# Show registration form
def register_view(request):
    return render(request, 'authentication/register.html')


# Show login form
def login_view(request):
    return render(request, 'authentication/login.html')


def register(request):
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        accept_terms = request.POST.get('accept_terms')

        if fullname and email and password and accept_terms:
            if User.objects.filter(email=email).exists():
                return HttpResponse("Email already registered.")

            # Create inactive user
            user = User(username=email, email=email, first_name=fullname)
            user.set_password(password)
            user.is_active = False
            user.save()

            # Generate token
            token = str(uuid.uuid4())

            # Create or update profile with token
            Profile.objects.update_or_create(user=user, defaults={'email_token': token})

            # Send email
            current_site = get_current_site(request)
            subject = "Email Verification"
            message = render_to_string('authentication/email_verification.html', {
                'user': user,
                'domain': current_site.domain,
                'token': token,
            })
            send_mail(subject, message, settings.EMAIL_HOST_USER, [email])

            return HttpResponse("Registration successful. Please check your email to verify your account.")
        else:
            return HttpResponse("Please fill all fields and accept the terms.")

    return render(request, 'authentication/register.html')


# Verify user email
def verify_email(request, token):
    try:
        profile = Profile.objects.get(email_token=token)
        user = profile.user
        user.is_active = True
        user.save()
        return render(request, 'authentication/verification_success.html', {'user': user})
    except Profile.DoesNotExist:
        return HttpResponse("Invalid or expired verification link.")


# Login view
def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=email)
        except User.DoesNotExist:
            return HttpResponse("No user found with this email.")

        if check_password(password, user.password):
            if user.is_active:
                auth_login(request, user)
                return redirect('dashboard')  # Make sure 'dashboard' is a valid named URL
            else:
                return HttpResponse("Please verify your email before logging in.")
        else:
            return HttpResponse("Invalid email or password.")

    return render(request, 'authentication/login.html')


# Dashboard view after login
@login_required
def home(request):
    title = "Dashboard"
    return render(request, 'dashboard.html', {'title': title})

#Admin User 
@login_required
def admin_user(request):
    title = "Users"
    users = User.objects.all()
    user_roles = Users_to_Roles.objects.all()
    roles = Role.objects.all()

# Create role dictionary {role_id: role_name}
    role_lookup = {role.id: role.name for role in roles}

# Map user_id to a list of role names
    user_roles_map = {}
    for ur in user_roles:
        user_roles_map.setdefault(ur.user_id, []).append(role_lookup.get(ur.roles_id))
    context = {
    'users': users,
    'user_roles_map': user_roles_map,
    'title': title,
    }
    return render(request, 'admin/users/index.html', context)




@csrf_exempt  # Optional if using CSRFToken in AJAX headers
def update_user(request, id):
    if request.method == 'POST':
        user = get_object_or_404(Profile, id=id)
        role = request.POST.get('role')
        is_active = request.POST.get('is_active')

        user.role = role
        user.is_active = bool(int(is_active))
        user.save()

        return JsonResponse({'message': 'User updated successfully.'})
    return JsonResponse({'error': 'Invalid request'}, status=400)
