from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
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

# === Questionnaires ===

@login_required
def questionnaires_list(request):
    from .models import Questionnaire, Trait
    
    if not Trait.objects.exists():
        default_traits = [
            'Komandinis darbas', 'Komunikabilumas', 'Iniciatyvumas', 'Problemų sprendimas', 'Lyderystė',
            'Analitinis mąstymas', 'Kūrybiškumas', 'Adaptabilumas', 'Atsakingumas', 'Laiko planavimas',
            'Techninės žinios', 'Strateginis mąstymas', 'Klientų aptarnavimas', 'Derybos', 'Prezentavimo įgūdžiai',
            'Patikimumas', 'Motyvacija', 'Pozityvumas', 'Efektyvumas', 'Savarankiškumas'
        ]
        for t in default_traits:
            Trait.objects.get_or_create(name=t)
            
    questionnaires = Questionnaire.objects.filter(created_by=request.user).order_by('-created_at')
    all_traits = Trait.objects.all().order_by('name')
    
    # Get team members for sending questionnaires
    team_members_qs = User.objects.none()
    try:
        user_company_link = request.user.profile.company_link
        if user_company_link:
            team_members_qs = User.objects.filter(profile__company_link=user_company_link).exclude(id=request.user.id)
        else:
             team_members_qs = User.objects.filter(profile__company_link__isnull=True).exclude(id=request.user.id)
    except Exception:
        team_members_qs = User.objects.filter(profile__isnull=True).exclude(id=request.user.id)
        
    team_members = team_members_qs.order_by('first_name', 'last_name')

    return render(request, 'questionnaires/list.html', {
        'questionnaires': questionnaires,
        'all_traits': all_traits,
        'team_members': team_members,
    })

@login_required
def create_questionnaire(request):
    from .models import Questionnaire, Trait
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            messages.error(request, 'Klausimyno pavadinimas yra privalomas.')
            return redirect('questionnaires_list')

        questionnaire = Questionnaire.objects.create(title=title, created_by=request.user)

        # Add existing traits
        trait_ids = request.POST.getlist('trait_ids')
        for tid in trait_ids:
            try:
                trait = Trait.objects.get(id=int(tid))
                questionnaire.traits.add(trait)
            except (Trait.DoesNotExist, ValueError):
                pass

        # Add custom traits
        custom_traits = request.POST.getlist('custom_traits')
        for name in custom_traits:
            name = name.strip()
            if name:
                trait, _ = Trait.objects.get_or_create(name=name, defaults={'created_by': request.user})
                questionnaire.traits.add(trait)

        messages.success(request, f'Klausimynas "{title}" sėkmingai sukurtas!')
    return redirect('questionnaires_list')


@login_required
@require_POST
def send_questionnaire(request):
    from .models import Questionnaire, FeedbackRequest
    from django.contrib.auth.models import User
    
    questionnaire_id = request.POST.get('questionnaire_id')
    colleague_id = request.POST.get('colleague_id')
    
    if not questionnaire_id or not colleague_id:
        messages.error(request, 'Trūksta duomenų klausimyno siuntimui.')
        return redirect('questionnaires_list')
        
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id, created_by=request.user)
    requested_to = get_object_or_404(User, id=colleague_id)
    
    # Check if a pending request already exists for this questionnaire and colleague
    existing = FeedbackRequest.objects.filter(
        requester=request.user,
        requested_to=requested_to,
        status='pending',
        project_name=questionnaire.title
    ).exists()
    
    if existing:
        messages.warning(request, f'Klausimynas "{questionnaire.title}" jau išsiųstas kolegai {requested_to.first_name} {requested_to.last_name} ir dar neužpildytas.')
        return redirect('questionnaires_list')
        
    FeedbackRequest.objects.create(
        requester=request.user,
        requested_to=requested_to,
        project_name=questionnaire.title, # Using title as project_name for now
        comment=f"Prašau užpildyti klausimyną: {questionnaire.title}",
        due_date=date.today()
    )
    
    messages.success(request, f'Klausimynas "{questionnaire.title}" sėkmingai išsiųstas kolegai {requested_to.first_name} {requested_to.last_name}.')
    return redirect('questionnaires_list')

@login_required
def delete_questionnaire(request, questionnaire_id):
    from .models import Questionnaire
    if request.method == 'POST':
        questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id, created_by=request.user)
        questionnaire.delete()
        messages.success(request, 'Klausimynas sėkmingai ištrintas.')
    return redirect('questionnaires_list')

@login_required
def questionnaire_statistics(request, questionnaire_id):
    from .models import Questionnaire, FeedbackRequest, Feedback
    from .services import FeedbackAnalytics

    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id, created_by=request.user)

    # Fetch feedback requests related to this questionnaire
    # For now, we linked them by using project_name=questionnaire.title
    feedback_requests = FeedbackRequest.objects.filter(
        requester=request.user,
        project_name=questionnaire.title,
        status='completed'
    )
    
    feedbacks = Feedback.objects.filter(feedback_request__in=feedback_requests)
    
    overall_avg_rating = feedbacks.aggregate(Avg('rating'))['rating__avg'] or 0
    received_feedback_count = feedbacks.count()
    
    competencies = [
        {'name': 'Komandinis darbas', 'score': feedbacks.aggregate(Avg('teamwork_rating'))['teamwork_rating__avg'] or 0},
        {'name': 'Komunikacija', 'score': feedbacks.aggregate(Avg('communication_rating'))['communication_rating__avg'] or 0},
        {'name': 'Iniciatyvumas', 'score': feedbacks.aggregate(Avg('initiative_rating'))['initiative_rating__avg'] or 0},
        {'name': 'Technologinės žinios', 'score': feedbacks.aggregate(Avg('technical_skills_rating'))['technical_skills_rating__avg'] or 0},
        {'name': 'Problemų sprendimas', 'score': feedbacks.aggregate(Avg('problem_solving_rating'))['problem_solving_rating__avg'] or 0},
    ]

    all_keywords = []
    for fb in feedbacks:
        if fb.keywords:
            keys = [k.strip() for k in fb.keywords.split(',') if k.strip()]
            all_keywords.extend(keys)

    all_keywords = list(set(all_keywords)) # Unique keywords

    strengths = []
    improvements = []
    
    # We can separate comments into strengths/improvements if we want, but for now we'll just list comments
    for fb in feedbacks:
        if fb.comments:
            strengths.append(fb.comments) 

    import json
    from django.db.models.functions import TruncDate

    chronological_feedbacks = feedbacks.annotate(
        date=TruncDate('feedback_request__created_at')
    ).values('date').annotate(
        avg_rating=Avg('rating'),
        avg_teamwork=Avg('teamwork_rating'),
        avg_communication=Avg('communication_rating'),
        avg_initiative=Avg('initiative_rating'),
        avg_technical=Avg('technical_skills_rating'),
        avg_problem_solving=Avg('problem_solving_rating')
    ).order_by('date')

    chart_labels = [fb['date'].strftime('%Y-%m-%d') if fb['date'] else 'Data nežinoma' for fb in chronological_feedbacks]
    
    chart_data = {
        'labels': chart_labels,
        'datasets': [
            {'label': 'Bendras', 'data': [round(fb['avg_rating'], 1) for fb in chronological_feedbacks], 'borderColor': '#8B5CF6', 'tension': 0.3},
            {'label': 'Komandinis darbas', 'data': [round(fb['avg_teamwork'], 1) for fb in chronological_feedbacks], 'borderColor': '#3B82F6', 'tension': 0.3, 'hidden': True},
            {'label': 'Komunikacija', 'data': [round(fb['avg_communication'], 1) for fb in chronological_feedbacks], 'borderColor': '#10B981', 'tension': 0.3, 'hidden': True},
            {'label': 'Iniciatyvumas', 'data': [round(fb['avg_initiative'], 1) for fb in chronological_feedbacks], 'borderColor': '#F59E0B', 'tension': 0.3, 'hidden': True},
            {'label': 'Technologinės žinios', 'data': [round(fb['avg_technical'], 1) for fb in chronological_feedbacks], 'borderColor': '#EF4444', 'tension': 0.3, 'hidden': True},
            {'label': 'Problemų sprendimas', 'data': [round(fb['avg_problem_solving'], 1) for fb in chronological_feedbacks], 'borderColor': '#6366F1', 'tension': 0.3, 'hidden': True},
        ]
    }

    context = {
        'questionnaire': questionnaire,
        'overall_avg_rating': round(overall_avg_rating, 1),
        'received_feedback_count': received_feedback_count,
        'competencies': competencies,
        'all_keywords': all_keywords,
        'strengths': strengths,
        'improvements': improvements,
        'chart_data_json': json.dumps(chart_data),
    }

    
    return render(request, 'questionnaires/statistics.html', context)
