from django.urls import path
from .views import (register_view, register,login , verify_email, login_view, 
home, admin_user, update_user,admin_role,
admin_team, delete_team, update_team, create_team,
task_index,task_create,profile_view)

urlpatterns = [

path('register/', register_view, name='register'),
path('sign_up/', register, name='sign_up'),
path('login/', login_view, name='login'),
path('sign_in/', login, name='sign_in'),
path('dashboard/', home, name='dashboard'),
path('verify/<str:token>/', verify_email, name='verify_email'),

#Admin Paths
path('users/', admin_user, name='users'),
path('user/update/<int:id>', update_user, name='update_user'),

path('roles/', admin_role, name='roles'),

path('teams/', admin_team, name='teams'),
path('teams/delete/<int:team_id>/', delete_team, name='delete_team'),
path('teams/update/<int:team_id>/', update_team, name='update_team'),
path('teams/create/', create_team, name='create_team'),

#Tasks Paths
path('tasks/', task_index, name='tasks'),
path('tasks/create/', task_create, name='tasks.create'),
path('profile/', profile_view, name='profile_view'),
]
