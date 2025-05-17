from django.urls import path
from .views import register_view, register,login , verify_email, login_view, home, admin_user, update_user,admin_role

urlpatterns = [

path('register/', register_view, name='register'),
path('sign_up/', register, name='sign_up'),
path('login/', login_view, name='login'),
path('sign_in/', login, name='sign_in'),
path('dashboard/', home, name='dashboard'),
path('verify/<str:token>/', verify_email, name='verify_email'),


path('users/', admin_user, name='users'),
path('user/update/<int:id>', update_user, name='update_user'),

path('roles/', admin_role, name='roles'),

]
