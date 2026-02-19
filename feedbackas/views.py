from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Count, Avg
from .forms import RegistrationForm, FeedbackForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .models import FeedbackRequest, Feedback
from users.models import Profile
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db import OperationalError
from django.views.decorators.http import require_POST
import json, traceback
from django.db.models import Avg
from django.db import models
import logging
from datetime import date
from .services import FeedbackGenerator, FeedbackAnalytics
from users.models import Department, Company
from .forms import DepartmentForm


logger = logging.getLogger(__name__)

def index(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, "index.html")

@login_required
def home(request):
    feedback_requests = FeedbackRequest.objects.filter(requested_to=request.user, status='pending')
    company_name = ''
    try:
        if request.user.profile.company_link:
            company_name = request.user.profile.company_link.name
    except (Profile.DoesNotExist, OperationalError):
        pass
    context = {
        'feedback_requests': feedback_requests,
        'company_name': company_name,
    }
    return render(request, 'home.html', context)

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            company_name = form.cleaned_data.get('company')
            company = None
            if company_name:
                company, created = Company.objects.get_or_create(name=company_name)
            Profile.objects.create(user=user, company_link=company)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')

@login_required
def get_team_members(request):
    user = request.user
    team_members_qs = User.objects.none()
    try:
        user_company_link = user.profile.company_link
        if user_company_link:
            team_members_qs = User.objects.filter(profile__company_link=user_company_link).exclude(id=user.id)
    except (Profile.DoesNotExist, OperationalError):
        pass  # Jei nėra įmonės, grąžinsime visus vartotojus žemiau
    if not team_members_qs.exists():
        team_members_qs = User.objects.exclude(id=user.id)
    data = [{'id': member.id, 'name': f'{member.first_name} {member.last_name}'} for member in team_members_qs]
    return JsonResponse(data, safe=False)

@login_required
def request_feedback(request):
    if request.method == 'POST':
        requester = request.user
        requested_to_id = request.POST.get('requested_to')
        project_name = request.POST.get('project_name')
        comment = request.POST.get('comment')
        due_date = request.POST.get('due_date')
        
        requested_to = get_object_or_404(User, id=requested_to_id)
        
        feedback_request = FeedbackRequest.objects.create(
            requester=requester,
            requested_to=requested_to,
            project_name=project_name,
            comment=comment,
            due_date=due_date
        )
        return JsonResponse({'success': True, 'feedback_request_id': feedback_request.id})
    return JsonResponse({'success': False, 'errors': 'Invalid request method'})

@login_required
def send_feedback(request, user_id):
    requester = get_object_or_404(User, id=user_id)
    requested_to = request.user
    
    feedback_request = FeedbackRequest.objects.create(
        requester=requester,
        requested_to=requested_to,
        project_name='Atsiliepimas',
        comment='',
        due_date=date.today()
    )
    
    return redirect('fill_feedback', request_id=feedback_request.id)

@login_required
def fill_feedback(request, request_id):
    feedback_request = get_object_or_404(FeedbackRequest, id=request_id)
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.feedback_request = feedback_request
            feedback.save()
            feedback_request.status = 'completed'
            feedback_request.save()
            return redirect('home')
    else:
        form = FeedbackForm()
    
    context = {
        'form': form,
        'feedback_request': feedback_request
    }
    return render(request, 'fill_feedback.html', context)



@login_required
def team_members_list(request):
    user = request.user
    team_members_qs = User.objects.none() 

    try:
        user_company_link = user.profile.company_link
        if user_company_link:
            # Filtruojame pagal įmonę ir atmetame patį vartotoją
            team_members_qs = User.objects.filter(profile__company_link=user_company_link).exclude(id=user.id)
        else:
            # Jei vartotojas neturi įmonės, rodome visus vartotojus be įmonės
            team_members_qs = User.objects.filter(profile__company_link__isnull=True).exclude(id=user.id)
    except Profile.DoesNotExist:
        # Jei vartotojas neturi profilio, rodome visus kitus vartotojus, kurie taip pat neturi profilio
        team_members_qs = User.objects.filter(profile__isnull=True).exclude(id=user.id)

    # Paieškos logika
    query = request.GET.get('q')
    if query:
        team_members_qs = team_members_qs.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

    # Anotuojame su papildomais duomenimis
    team_members = team_members_qs.select_related('profile').annotate(
        average_rating=Avg('made_requests__feedback__rating')
    )

    # Bendra statistika
    overall_avg_rating = Feedback.objects.filter(feedback_request__requester__in=team_members_qs).aggregate(Avg('rating'))['rating__avg']
    pending_feedback_count = FeedbackRequest.objects.filter(requester__in=team_members_qs, status='pending').count()

    context = {
        'team_members': team_members,
        'search_query': query,
        'overall_avg_rating': overall_avg_rating,
        'pending_feedback_count': pending_feedback_count,
    }
    
    return render(request, 'feedbackas/team_members_list.html', context)

@login_required
def my_tasks_list(request):
    # Feedback requests made by the current user
    made_requests = FeedbackRequest.objects.filter(requester=request.user).order_by('-due_date')

    # Feedback requests assigned to the current user (tasks to do)
    assigned_requests = FeedbackRequest.objects.filter(requested_to=request.user).order_by('-due_date')

    context = {
        'made_requests': made_requests,
        'assigned_requests': assigned_requests,
    }
    return render(request, 'my_tasks.html', context)




@login_required
@require_POST
def generate_ai_feedback(request):
    try:
        data = json.loads(request.body)
        ratings = data.get('ratings', {})
        keywords = data.get('keywords', '')
        comments = data.get('comments', '')
        existing_feedback = data.get('existing_feedback', '')
        colleague_name = data.get('colleague_name', 'Kolega')

        generated_text = FeedbackGenerator.generate(
            ratings=ratings,
            keywords=keywords,
            comments=comments,
            existing_feedback=existing_feedback,
            colleague_name=colleague_name
        )
        
        return JsonResponse({'generated_feedback': generated_text})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"AI feedback generation failed: {e}\n{traceback.format_exc()}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_feedback_data(request):
    user = request.user
    # Suskaičiuojame tik užpildytas apklausas
    completed_requests_count = FeedbackRequest.objects.filter(requester=user, status='completed').count()
    
    data = []
    # Pirmieji taškai bus 'done' (pilnaviduriai)
    for i in range(completed_requests_count):
        data.append({
            'id': None, # Šiuo atveju ID nereikalingas, nes nekeičiame logikos
            'label': f'Apklausa {i + 1}',
            'status': 'done'
        })
        
    # Likę taškai bus 'empty' (tušti)
    for i in range(completed_requests_count, 8):
        data.append({
            'id': None,
            'label': f'Apklausa {i + 1}',
            'status': 'empty'
        })
    return JsonResponse(data, safe=False)


@login_required
def results(request):
    user = request.user
    stats = FeedbackAnalytics.get_user_stats(user)
    
    company_name = ''
    if hasattr(request.user, 'profile') and request.user.profile.company_link:
        company_name = request.user.profile.company_link.name

    context = {
        **stats,
        'company_name': company_name,
    }
    
    return render(request, 'results.html', context)

@login_required
def all_feedback_list(request):
    # Fetch all completed feedback, ordered by the newest first.
    # Using select_related to optimize DB queries by fetching related objects in a single query.
    all_feedback = Feedback.objects.select_related(
        'feedback_request__requester', 
        'feedback_request__requested_to'
    ).filter(feedback_request__status='completed').order_by('-feedback_request__created_at')

    context = {
        'all_feedback': all_feedback,
    }
    return render(request, 'all_feedback_list.html', context)

@login_required
def company_management(request):
    user = request.user
    try:
        user_company = user.profile.company_link
    except AttributeError:
        # Fallback jei dar nėra susieto Company objekto
        return render(request, 'company_management.html', {'error': 'Jūs nepriskirtas jokiai įmonei.'})

    if not user_company:
         return redirect('home') # Arba error page

    # Formos apdorojimas (Pridėti departamentą)
    if request.method == 'POST':
        form = DepartmentForm(user, request.POST)
        if form.is_valid():
            department = form.save(commit=False)
            department.company = user_company
            department.save()
            return redirect('company_management')
    else:
        form = DepartmentForm(user)

    # Gauname tik šaknijinius departamentus (kurie neturi tėvo)
    # Vaikus gausime template su rekursija arba prefetch_related
    root_departments = Department.objects.filter(company=user_company, parent__isnull=True).prefetch_related('sub_departments')
    
    # Gauname darbuotojus be departamento, kad galėtume juos priskirti
    unassigned_users = User.objects.filter(profile__company_link=user_company, profile__department__isnull=True)

    context = {
        'root_departments': root_departments,
        'form': form,
        'unassigned_users': unassigned_users,
        'company_name': user_company.name
    }
    return render(request, 'company_management.html', context)

from django.contrib.auth.decorators import user_passes_test

@user_passes_test(lambda u: u.is_superuser)
def superadmin_dashboard(request):
    # Statistics
    total_users = User.objects.count()
    total_companies = Company.objects.count()
    pending_feedback_count = FeedbackRequest.objects.filter(status='pending').count()
    completed_feedback_count = FeedbackRequest.objects.filter(status='completed').count()

    # Recent Data
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_companies = Company.objects.order_by('-created_at')[:5]

    context = {
        'total_users': total_users,
        'total_companies': total_companies,
        'pending_feedback_count': pending_feedback_count,
        'completed_feedback_count': completed_feedback_count,
        'recent_users': recent_users,
        'recent_companies': recent_companies,
    }
    return render(request, 'superadmin/dashboard.html', context)

@user_passes_test(lambda u: u.is_superuser)
def superadmin_companies_list(request):
    companies = Company.objects.annotate(employee_count=Count('profile')).order_by('-created_at')
    
    context = {
        'companies': companies,
    }
    return render(request, 'superadmin/companies_list.html', context)

@user_passes_test(lambda u: u.is_superuser)
def superadmin_company_detail(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    employee_count = company.profile_set.count() # Accessing related profiles via default reverse relation
    department_count = company.departments.count()

    context = {
        'company': company,
        'employee_count': employee_count,
        'department_count': department_count,
    }
    return render(request, 'superadmin/company_detail.html', context)

@user_passes_test(lambda u: u.is_superuser)
def superadmin_edit_hierarchy(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    
    # Passing a dummy user to DepartmentForm init is necessary because it expects a user 
    # to filter queryset for parent departments. 
    # Ideally DepartmentForm should be refactored to accept querysets directly, 
    # but for now we can rely on how it filters using user.profile.company_link.
    # HOWEVER, since we are superadmin, we don't have a company link matching the target company necessarily.
    # We need to instantiate the form and then manually override the parent queryset.
    
    if request.method == 'POST':
        form = DepartmentForm(request.user, request.POST)
        # Override parent queryset to target company's departments
        form.fields['parent'].queryset = Department.objects.filter(company=company)
        
        if form.is_valid():
            department = form.save(commit=False)
            department.company = company
            department.save()
            return redirect('superadmin_edit_hierarchy', company_id=company_id)
    else:
        form = DepartmentForm(request.user)
        form.fields['parent'].queryset = Department.objects.filter(company=company)

    root_departments = Department.objects.filter(company=company, parent__isnull=True).prefetch_related('sub_departments')

    context = {
        'company': company,
        'form': form,
        'root_departments': root_departments,
    }
    return render(request, 'superadmin/edit_hierarchy.html', context)

@user_passes_test(lambda u: u.is_superuser)
def superadmin_edit_employees(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    profiles = Profile.objects.filter(company_link=company).select_related('user', 'department', 'manager')
    
    context = {
        'company': company,
        'profiles': profiles,
    }
    return render(request, 'superadmin/edit_employees.html', context)

@user_passes_test(lambda u: u.is_superuser)
def superadmin_add_employee(request, company_id):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            if hasattr(user, 'profile'):
                if user.profile.company_link:
                    messages.error(request, f'Vartotojas {email} jau priklauso įmonei {user.profile.company_link.name}.')
                else:
                    company = get_object_or_404(Company, id=company_id)
                    user.profile.company_link = company
                    user.profile.save()
                    messages.success(request, f'Vartotojas {email} sėkmingai pridėtas prie įmonės.')
            else:
                 # If user has no profile, create one
                company = get_object_or_404(Company, id=company_id)
                Profile.objects.create(user=user, company_link=company)
                messages.success(request, f'Vartotojas {email} sėkmingai pridėtas prie įmonės.')

        except User.DoesNotExist:
            messages.error(request, f'Vartotojas su el. paštu {email} nerastas.')
    
    return redirect('superadmin_edit_employees', company_id=company_id)

@user_passes_test(lambda u: u.is_superuser)
def superadmin_delete_department(request, company_id, department_id):
    if request.method == 'POST':
        company = get_object_or_404(Company, id=company_id)
        department = get_object_or_404(Department, id=department_id, company=company)
        
        department.delete()
        messages.success(request, f'Departamentas "{department.name}" sėkmingai ištrintas.')
            
    return redirect('superadmin_edit_hierarchy', company_id=company_id)

@user_passes_test(lambda u: u.is_superuser)
def superadmin_remove_employee(request, company_id, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if hasattr(user, 'profile') and user.profile.company_link_id == company_id:
            user.profile.company_link = None
            user.profile.department = None
            user.profile.manager = None
            user.profile.save()
            messages.success(request, f'Vartotojas {user.email} pašalintas iš įmonės.')
        else:
            messages.error(request, 'Vartotojas nepriklauso šiai įmonei.')
            
    return redirect('superadmin_edit_employees', company_id=company_id)

@user_passes_test(lambda u: u.is_superuser)
def superadmin_impersonate_user(request, user_id):
    original_user_id = request.user.id
    target_user = get_object_or_404(User, id=user_id)
    
    # Log in as the target user without authentication backend check
    # We specify the backend manually to bypass authentication
    login(request, target_user, backend='django.contrib.auth.backends.ModelBackend')

    # Save the original user's ID in the session AFTER login because login flushes session
    request.session['impersonator_id'] = original_user_id
    
    return redirect('home')

def stop_impersonation(request):
    impersonator_id = request.session.get('impersonator_id')
    
    if impersonator_id:
        original_user = get_object_or_404(User, id=impersonator_id)
        
        # Log in back as the original user
        login(request, original_user, backend='django.contrib.auth.backends.ModelBackend')
        
        # Remove the impersonator ID from the session
        del request.session['impersonator_id']
        
        return redirect('superadmin_dashboard')
        
    return redirect('home')