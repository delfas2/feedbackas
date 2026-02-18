"""
URL configuration for feedbackas project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('get_team_members/', views.get_team_members, name='get_team_members'),
    path('request_feedback/', views.request_feedback, name='request_feedback'),
    path('send_feedback/<int:user_id>/', views.send_feedback, name='send_feedback'),
    path('feedback/fill/<int:request_id>/', views.fill_feedback, name='fill_feedback'),
    path('team/', views.team_members_list, name='team_members_list'),
    path('tasks/dashboard/', views.my_tasks_list, name='my_tasks_list'),
    path('results/', views.results, name='results'),
    path('generate_ai_feedback/', views.generate_ai_feedback, name='generate_ai_feedback'),
    path('all_feedback/', views.all_feedback_list, name='all_feedback_list'),
    path('get_feedback_data/', views.get_feedback_data, name='get_feedback_data'),
    path('management/', views.company_management, name='company_management'),
]
