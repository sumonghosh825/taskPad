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

from .models import Profile, Role, Users_to_Roles, Teams, Projects
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

    # Prepare list of users with their roles
    user_with_roles = []
    for u in users:
        role_list = user_roles_map.get(u.id, [])
        user_with_roles.append({
            'user': u,
            'roles': role_list,
        })

    context = {
        'user_with_roles': user_with_roles,
        'title': title,
    }
    return render(request, 'admin/users/index.html', context)




@csrf_exempt  # Optional if using CSRFToken in AJAX headers
def update_user(request, id):
    if request.method == 'POST':
        user = get_object_or_404(Profile, id=id)
        user_role = get_object_or_404(Users_to_Roles, user_id = id)
        role = request.POST.get('role')
        is_active = request.POST.get('is_active')

        user_role.roles_id = role
        user.is_active = bool(int(is_active))
        user.save()
        user_role.save()
        return JsonResponse({'message': 'User updated successfully.'})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def admin_role(request):
    title = "Roles"
    roles = Role.objects.all()

    # Get all user IDs from roles
    user_ids = [role.created_by for role in roles if role.created_by]

    # Fetch all users matching those IDs
    users = User.objects.filter(id__in=user_ids)
    user_map = {user.id: user for user in users}

    # Attach matched creator to each role
    roles_with_creator = []
    for role in roles:
        creator = user_map.get(role.created_by)
        roles_with_creator.append({
            'role': role,
            'creator': creator
        })

    context = {
        'title': title,
        'roles_with_creator': roles_with_creator,
    }
    return render(request, 'admin/roles/index.html', context)


@login_required
def admin_team(request):
    title = "Teams"
    teams = Teams.objects.all()
    users = User.objects.all()

    # Step 1: Collect all created_by user IDs from the teams
    creator_ids = [team.created_by for team in teams if team.created_by]

    # Step 2: Fetch user objects in bulk
    creators = User.objects.filter(id__in=creator_ids)
    creator_map = {user.id: user for user in creators}

    teams_data = []

    for team in teams:
        # Step 3: Resolve members
        member_names = []
        if team.member:
            member_ids = [int(uid) for uid in team.member.split(',') if uid.strip().isdigit()]
            member_users = User.objects.filter(id__in=member_ids)
            member_names = [user.first_name for user in member_users]

        # Step 4: Resolve created_by user
        creator = creator_map.get(team.created_by)
        creator_name = f"{creator.first_name} {creator.last_name}" if creator else "N/A"

        # Step 5: Append final data
        teams_data.append({
            'id': team.id,
            'name': team.name,
            'status': team.status,
            'members': member_names,
            'created_by': creator_name,
        })

    return render(request, 'admin/teams/index.html', {
        'title': title,
        'teams_data': teams_data,
        'users': users,
    })

@login_required
def create_team(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('team_name') or None
            status_str = request.POST.get('status')
            status = True if status_str == '1' else False if status_str == '0' else None
            members = request.POST.getlist('members')
            members_str = ','.join(members) if members else None
            created_by = request.user.id
            Teams.objects.create(
                name=name,
                status=status,
                member=members_str,
                created_by=created_by
            )

            return JsonResponse({'success': True, 'message': 'Team created successfully'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)


@login_required
def update_team(request, team_id):
    team = get_object_or_404(Teams, id=team_id)

    if request.method == 'POST':
        team.name = request.POST.get('team_name') or team.name
        team.status = request.POST.get('status') == '1'
        members = request.POST.getlist('members')
        team.members = ','.join(members) if members else None
        team.save()

    return redirect('teams')


@login_required
def delete_team(request, team_id):
    team = get_object_or_404(Teams, id=team_id)
    team.delete()
    return redirect('teams')

#Task Pages
@login_required
def task_index(request):
    title = "Tasks"
    return render(request, 'tasks/index.html', {'title': title})

@login_required
def task_create(request):
    title = "Tasks Create"
    return render(request, 'tasks/create.html', {'title': title})


