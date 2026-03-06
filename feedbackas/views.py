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
from .services import FeedbackAnalytics
from .ai_service import FeedbackGenerator
from users.models import Department, Company
from .forms import DepartmentForm
from django.utils import timezone


logger = logging.getLogger(__name__)

def is_company_active(user):
    if hasattr(user, 'profile') and user.profile.company_link:
        return user.profile.company_link.is_active
    return True

def index(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        # Here we could process request.POST.get('name'), email, message 
        # and send an email or save to DB. For now we just show success.
        messages.success(request, 'Ačiū! Jūsų užklausa gauta, netrukus su jumis susisieksime.')
        return redirect('index')
        
    return render(request, 'index.html')

def apie_mus(request):
    return render(request, 'apie_mus.html')

@login_required
def home(request):
    feedback_requests = FeedbackRequest.objects.filter(requested_to=request.user, status='pending').select_related('requester', 'requester__profile')
    company_name = ''
    try:
        if request.user.profile.company_link:
            company_name = request.user.profile.company_link.name
    except Profile.DoesNotExist:
        pass
    except OperationalError as e:
        logger.error(f"Database operational error fetching company for {request.user.username}: {e}")
    
    # Recent team activity
    recent_activity = []
    
    # Recent feedbacks received about this user
    recent_received = Feedback.objects.filter(
        feedback_request__requester=request.user,
        feedback_request__status='completed'
    ).select_related('feedback_request__requested_to').order_by('-feedback_request__created_at')[:5]
    for fb in recent_received:
        person = fb.feedback_request.requested_to
        recent_activity.append({
            'initials': (person.first_name[:1] + person.last_name[:1]).upper() if person.first_name and person.last_name else '??',
            'name': person.get_full_name(),
            'action': f'pateikė atsiliepimą apie jus.',
            'date': fb.feedback_request.created_at,
        })
    
    # Recent pending requests for this user
    recent_pending = FeedbackRequest.objects.filter(
        requested_to=request.user,
        status='pending'
    ).select_related('requester').order_by('-created_at')[:5]
    for fr in recent_pending:
        person = fr.requester
        recent_activity.append({
            'initials': (person.first_name[:1] + person.last_name[:1]).upper() if person.first_name and person.last_name else '??',
            'name': person.get_full_name(),
            'action': f'paprašė jūsų atsiliepimo.',
            'date': fr.created_at,
        })
    
    # Sort by date descending, take top 5
    recent_activity.sort(key=lambda x: x['date'], reverse=True)
    recent_activity = recent_activity[:5]
    
    # Dynamic metrics calculation
    pending_tasks_count = feedback_requests.count()
    
    completed_surveys_count = Feedback.objects.filter(
        feedback_request__requested_to=request.user, 
        feedback_request__status='completed'
    ).count()
    
    my_team_count = 0
    if hasattr(request.user, 'profile') and request.user.profile.department:
        my_team_count = Profile.objects.filter(
            department=request.user.profile.department,
            company_link=request.user.profile.company_link
        ).exclude(user=request.user).count()

    context = {
        'feedback_requests': feedback_requests,
        'company_name': company_name,
        'recent_activity': recent_activity,
        'is_company_active': is_company_active(request.user),
        'pending_tasks_count': pending_tasks_count,
        'completed_surveys_count': completed_surveys_count,
        'my_team_count': my_team_count,
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
    except Profile.DoesNotExist:
        pass  # Jei nėra įmonės, grąžinsime visus vartotojus žemiau
    except OperationalError as e:
        logger.error(f"Database error fetching team_members for {user.username}: {e}")
    if not team_members_qs.exists():
        team_members_qs = User.objects.exclude(id=user.id)
    data = [{'id': member.id, 'name': member.get_full_name() or member.username} for member in team_members_qs]
    return JsonResponse(data, safe=False)

@login_required
def request_feedback(request):
    if not is_company_active(request.user):
        return JsonResponse({'success': False, 'errors': 'Jūsų įmonė yra išjungta. Veiksmas negalimas.'})
        
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
    if not is_company_active(request.user):
        messages.error(request, 'Jūsų įmonė yra išjungta. Veiksmas negalimas.')
        return redirect('home')
        
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
    if not is_company_active(request.user):
        messages.error(request, 'Jūsų įmonė yra išjungta. Veiksmas negalimas.')
        return redirect('home')
        
    feedback_request = get_object_or_404(FeedbackRequest, id=request_id)
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.feedback_request = feedback_request
            
            # Išsaugome atsiliepimą, kad turėtume jo ID
            feedback.save()
            feedback_request.status = 'completed'
            feedback_request.save()
            
            # AI Išskyrimas (Stiprybės ir Tobulintinos sritys) - Foninė užduotis
            from django_q.tasks import async_task
            async_task('feedbackas.services.extract_feedback_features_task', feedback.id)
            
            # Save trait ratings if this is a questionnaire-based feedback
            if feedback_request.questionnaire:
                from .models import TraitRating, Trait
                for trait in feedback_request.questionnaire.traits.all():
                    trait_rating_value = request.POST.get(f'trait_rating_{trait.id}', 0)
                    try:
                        trait_rating_value = int(trait_rating_value)
                    except (ValueError, TypeError):
                        trait_rating_value = 0
                    TraitRating.objects.create(
                        feedback=feedback,
                        trait=trait,
                        rating=trait_rating_value
                    )
            
            return redirect('home')
    else:
        form = FeedbackForm()
    
    # If this feedback request is linked to a questionnaire, pass its traits
    import json
    questionnaire_traits = []
    if feedback_request.questionnaire:
        questionnaire_traits = [
            {'id': t.id, 'name': t.name}
            for t in feedback_request.questionnaire.traits.all()
        ]
    
    context = {
        'form': form,
        'feedback_request': feedback_request,
        'questionnaire_traits_json': json.dumps(questionnaire_traits),
        'has_questionnaire': feedback_request.questionnaire is not None,
    }
    return render(request, 'fill_feedback.html', context)



@login_required
def team_members_list(request):
    user = request.user
    team_members_qs = User.objects.none() 

    try:
        user_department = user.profile.department
        user_company_link = user.profile.company_link
        
        # Check if user manages any department with sub-departments
        managed_departments = Department.objects.filter(manager=user)
        sub_departments = Department.objects.filter(parent__in=managed_departments)
        
        if sub_departments.exists():
            # Hierarchical mode: show department blocks
            department_blocks = []
            
            # Sub-departments loop optimization
            for dept in sub_departments.select_related('manager').prefetch_related('members__user'):
                members_qs = User.objects.filter(profile__department=dept).select_related('profile').annotate(
                    average_rating=Avg('made_requests__feedback__rating')
                )
                
                # Fetch department avg with a single database hit using filter instead of evaluating qs
                dept_avg = Feedback.objects.filter(
                    feedback_request__requester__profile__department=dept,
                    feedback_request__status='completed'
                ).aggregate(Avg('rating'))['rating__avg']
                
                department_blocks.append({
                    'department': dept,
                    'members': members_qs,
                    'member_count': members_qs.count(),
                    'avg_rating': round(dept_avg, 2) if dept_avg else None,
                })
            
            # Also include direct members of the managed department (not in sub-depts)
            for managed_dept in managed_departments:
                direct_members = User.objects.filter(profile__department=managed_dept).exclude(id=user.id).select_related('profile').annotate(
                    average_rating=Avg('made_requests__feedback__rating')
                )
                if direct_members.exists():
                    direct_avg = Feedback.objects.filter(
                        feedback_request__requester__profile__department=managed_dept,
                        feedback_request__status='completed'
                    ).exclude(feedback_request__requester=user).aggregate(Avg('rating'))['rating__avg']
                    
                    department_blocks.insert(0, {
                        'department': managed_dept,
                        'members': direct_members,
                        'member_count': direct_members.count(),
                        'avg_rating': round(direct_avg, 2) if direct_avg else None,
                    })
            
            # Overall stats
            all_members = User.objects.filter(
                Q(profile__department__in=sub_departments) | 
                Q(profile__department__in=managed_departments)
            ).exclude(id=user.id)
            overall_avg_rating = Feedback.objects.filter(
                feedback_request__requester__in=all_members, 
                feedback_request__status='completed'
            ).aggregate(Avg('rating'))['rating__avg']
            pending_feedback_count = FeedbackRequest.objects.filter(
                requester__in=all_members, status='pending'
            ).count()
            
            context = {
                'has_sub_departments': True,
                'department_blocks': department_blocks,
                'team_members': all_members,
                'search_query': None,
                'overall_avg_rating': overall_avg_rating,
                'pending_feedback_count': pending_feedback_count,
            }
            return render(request, 'feedbackas/team_members_list.html', context)
        
        # Flat mode: show single department members
        if user_department:
            team_members_qs = User.objects.filter(profile__department=user_department).exclude(id=user.id)
        elif user_company_link:
            team_members_qs = User.objects.filter(profile__company_link=user_company_link, profile__department__isnull=True).exclude(id=user.id)
        else:
            team_members_qs = User.objects.filter(profile__company_link__isnull=True).exclude(id=user.id)
    except Profile.DoesNotExist:
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
        'has_sub_departments': False,
        'team_members': team_members,
        'search_query': query,
        'overall_avg_rating': overall_avg_rating,
        'pending_feedback_count': pending_feedback_count,
    }
    
    return render(request, 'feedbackas/team_members_list.html', context)

@login_required
def my_tasks_list(request):
    # Feedback requests made by the current user
    made_requests = FeedbackRequest.objects.filter(requester=request.user).select_related('requested_to', 'feedback').order_by('-due_date')

    # Feedback requests assigned to the current user (tasks to do)
    assigned_requests = FeedbackRequest.objects.filter(requested_to=request.user).select_related('requester').order_by('-due_date')

    context = {
        'made_requests': made_requests,
        'assigned_requests': assigned_requests,
    }
    return render(request, 'my_tasks.html', context)

@login_required
@require_POST
def cancel_feedback_request(request, request_id):
    """
    Suteikia galimybę atšaukti (ištrinti) prašymą, kol jis dar nėra 'completed'.
    """
    feedback_request = get_object_or_404(FeedbackRequest, id=request_id)

    # Patikriname ar esamas vartotojas yra prašymo autorius
    if feedback_request.requester != request.user:
        messages.error(request, 'Neturite teisių atšaukti šio prašymo.')
        return redirect('my_tasks_list')
        
    # Patikriname ar prašymas dar nebaigtas (galima atšaukti tik 'pending')
    if feedback_request.status != 'pending':
        messages.error(request, 'Negalima atšaukti jau įvertinto arba užbaigto prašymo.')
        return redirect('my_tasks_list')

    # Jei viskas gerai - triname
    feedback_request.delete()
    messages.success(request, 'Atsiliepimo prašymas sėkmingai atšauktas.')
    
    return redirect('my_tasks_list')

@login_required
def edit_feedback_request(request, request_id):
    """
    Leidžia vartotojui paredaguoti prašymo projekto pavadinimą, komentarą ir terminą.
    """
    feedback_request = get_object_or_404(FeedbackRequest, id=request_id)

    # Autoriaus ir statuso patikrinimai
    if feedback_request.requester != request.user:
        messages.error(request, 'Neturite teisių redaguoti šio prašymo.')
        return redirect('my_tasks_list')
        
    if feedback_request.status != 'pending':
        messages.error(request, 'Begalima redaguoti jau įvertinto arba užbaigto prašymo.')
        return redirect('my_tasks_list')
        
    if request.method == 'POST':
        project_name = request.POST.get('project_name')
        comment = request.POST.get('comment')
        due_date = request.POST.get('due_date')
        
        if project_name and due_date:
            feedback_request.project_name = project_name
            feedback_request.comment = comment
            feedback_request.due_date = due_date
            feedback_request.save()
            messages.success(request, 'Atsiliepimo prašymas sėkmingai atnaujintas.')
        else:
            messages.error(request, 'Užpildykite visus privalomus laukus (Projekto pavadinimas, Terminas).')

    return redirect('my_tasks_list')




from django_ratelimit.decorators import ratelimit

from django_q.tasks import async_task, result

@login_required
@require_POST
@ratelimit(key='user', rate='10/10m', block=True)
def generate_ai_feedback(request):
    try:
        data = json.loads(request.body)
        ratings = data.get('ratings', {})
        keywords = data.get('keywords', '')
        comments = data.get('comments', '')
        existing_feedback = data.get('existing_feedback', '')
        colleague_name = data.get('colleague_name', 'Kolega')

        task_id = async_task(
            'feedbackas.services.generate_ai_feedback_task',
            ratings=ratings,
            keywords=keywords,
            comments=comments,
            existing_feedback=existing_feedback,
            colleague_name=colleague_name
        )
        
        return JsonResponse({'task_id': task_id, 'status': 'processing'})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"AI feedback dispatch failed: {e}\n{traceback.format_exc()}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def check_ai_task_status(request):
    task_id = request.GET.get('task_id')
    if not task_id:
        return JsonResponse({'error': 'No task_id provided'}, status=400)
        
    try:
        from django_q.models import Task
        task = Task.get_task(task_id)
        if task is None:
            return JsonResponse({'status': 'processing'})
            
        if task.success:
            return JsonResponse({'status': 'completed', 'generated_feedback': task.result})
        else:
            return JsonResponse({'status': 'failed', 'error': 'Task failed to execute'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_feedback_data(request):
    user = request.user
    # Get all feedback requests made by this user, ordered by creation date
    all_requests = FeedbackRequest.objects.filter(
        requester=user
    ).select_related('requested_to', 'feedback').order_by('created_at')
    
    data = []
    for fr in all_requests:
        respondent = fr.requested_to.get_full_name() or fr.requested_to.username
        label = f"{fr.project_name} ({respondent})"
        
        feedback_details = None
        if fr.status == 'completed':
            status = 'done'
            try:
                # Accessing a missing OneToOneField can raise RelatedObjectDoesNotExist
                if fr.feedback:
                    feedback_details = {
                        'project': fr.project_name,
                        'rname': respondent,
                        'rating': fr.feedback.rating,
                        'date': fr.feedback.created_at.strftime('%Y-%m-%d'),
                        'feedback': fr.feedback.feedback,
                        'comments': fr.feedback.comments,
                    }
            except Exception:
                pass
        elif fr.status == 'pending':
            status = 'active'
        else:
            status = 'empty'
            
        data.append({
            'id': fr.id,
            'label': label,
            'status': status,
            'feedback_details': feedback_details
        })
    
    return JsonResponse(data, safe=False)


@login_required
def results(request):
    user = request.user
    period = request.GET.get('period', 'all')
    stats = FeedbackAnalytics.get_user_stats(user, period=period)
    
    company_name = ''
    if hasattr(request.user, 'profile') and request.user.profile.company_link:
        company_name = request.user.profile.company_link.name

    context = {
        **stats,
        'company_name': company_name,
        'current_period': period,
    }
    
    return render(request, 'results.html', context)


@login_required
def get_competency_trend(request, competency_name):
    """
    Returns the historical evaluation scores for a specific competency for the current user.
    Uses the actual DB rating fields (teamwork_rating, communication_rating, etc.)
    """
    user = request.user

    # Map Lithuanian competency display names to DB field names
    competency_field_map = {
        'komandinis darbas': 'teamwork_rating',
        'komunikacija': 'communication_rating',
        'iniciatyvumas': 'initiative_rating',
        'techninės žinios': 'technical_skills_rating',
        'problemų sprendimas': 'problem_solving_rating',
    }

    field_name = competency_field_map.get(competency_name.strip().lower())
    if not field_name:
        return JsonResponse({'competency': competency_name, 'trend': []})

    # Get all completed feedback for this user (they are the requester)
    feedbacks = Feedback.objects.filter(
        feedback_request__requester=user,
        feedback_request__status='completed'
    ).select_related('feedback_request').order_by('feedback_request__created_at')

    trend_data = []
    for fb in feedbacks:
        score_val = getattr(fb, field_name, None)
        if score_val is not None:
            trend_data.append({
                'date': fb.feedback_request.created_at.strftime('%Y-%m-%d'),
                'score': float(score_val),
                'project': fb.feedback_request.project_name
            })

    return JsonResponse({'competency': competency_name, 'trend': trend_data})


@login_required
def team_statistics(request):
    user = request.user
    
    # Find departments managed by this user
    managed_departments = Department.objects.filter(manager=user)
    if not managed_departments.exists():
        from django.contrib import messages as django_messages
        django_messages.warning(request, 'Jūs nesate jokio padalinio vadovas.')
        return redirect('home')
    
    department = managed_departments.first()
    team_members = User.objects.filter(profile__department=department).exclude(id=user.id)
    
    # Aggregate stats using TeamAnalytics service
    from .services import TeamAnalytics
    stats = TeamAnalytics.get_team_stats(team_members)

    context = {
        'department': department,
        'member_stats': stats['member_stats'],
        'team_avg_rating': round(stats['team_avg_rating'], 2),
        'team_feedback_count': stats['team_feedback_count'],
        'team_member_count': stats['team_member_count'],
        'competencies': stats['competencies'],
    }
    return render(request, 'team_statistics.html', context)

@login_required
def team_member_detail(request, user_id):
    member = get_object_or_404(User, id=user_id)
    
    # Verify current user is a manager of the member's department or a parent department
    member_dept = member.profile.department if hasattr(member, 'profile') else None
    is_authorized = False
    if member_dept:
        # Check direct manager
        if member_dept.manager == request.user:
            is_authorized = True
        else:
            # Walk up the parent chain
            parent = member_dept.parent
            while parent:
                if parent.manager == request.user:
                    is_authorized = True
                    break
                parent = parent.parent
    if not is_authorized:
        from django.contrib import messages as django_messages
        django_messages.error(request, 'Jūs neturite teisės peržiūrėti šio darbuotojo informacijos.')
        return redirect('home')
    
    # All completed feedback about this member
    feedbacks = Feedback.objects.filter(
        feedback_request__requester=member,
        feedback_request__status='completed'
    ).select_related('feedback_request', 'feedback_request__requested_to').order_by('-feedback_request__created_at')
    
    # Aggregate stats using TeamAnalytics service
    from .services import TeamAnalytics
    stats = TeamAnalytics.get_member_detailed_stats(feedbacks)
    
    # Trait ratings (from questionnaire-based feedback)
    from .models import TraitRating
    trait_ratings = TraitRating.objects.filter(
        feedback__feedback_request__requester=member
    ).select_related('trait').values('trait__name').annotate(
        avg_rating=Avg('rating')
    ).order_by('-avg_rating')
    
    context = {
        'member': member,
        'department': member_dept,
        'feedbacks': feedbacks,
        'avg_rating': stats['avg_rating'],
        'feedback_count': feedbacks.count(),
        'competencies': stats['competencies'],
        'all_keywords': list(stats['keywords'])[:15],
        'trait_ratings': trait_ratings,
    }
    return render(request, 'team_member_detail.html', context)

@login_required
def all_feedback_list(request):
    # Fetch only feedback received about the current user
    all_feedback = Feedback.objects.select_related(
        'feedback_request__requester', 
        'feedback_request__requested_to'
    ).filter(
        feedback_request__requester=request.user,
        feedback_request__status='completed'
    ).order_by('-feedback_request__created_at')

    context = {
        'all_feedback': all_feedback,
    }
    return render(request, 'all_feedback_list.html', context)

@login_required
def company_management(request):
    user = request.user
    
    # Saugumas: Patikrinimas ar vartotojas turi teises
    if not user.is_superuser and not getattr(user.profile, 'is_company_admin', False):
        from django.contrib import messages
        messages.error(request, 'Neturite teisių valdyti įmonės struktūros.')
        return redirect('home')

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
            # Auto-assign manager to this department
            if department.manager:
                manager_profile = department.manager.profile
                manager_profile.department = department
                manager_profile.save()
            return redirect('company_management')
    else:
        form = DepartmentForm(user)

    # Gauname tik šaknijinius departamentus (kurie neturi tėvo)
    # Vaikus gausime template su rekursija arba prefetch_related
    root_departments = Department.objects.filter(company=user_company, parent__isnull=True).prefetch_related('sub_departments')
    
    # Gauname darbuotojus be departamento, kad galėtume juos priskirti
    unassigned_users = User.objects.filter(profile__company_link=user_company, profile__department__isnull=True)

    # All departments for the assignment dropdown
    all_departments = Department.objects.filter(company=user_company).order_by('name')

    context = {
        'root_departments': root_departments,
        'form': form,
        'unassigned_users': unassigned_users,
        'company_name': user_company.name,
        'all_departments': all_departments,
    }
    return render(request, 'company_management.html', context)

@login_required
def assign_to_department(request):
    if request.method == 'POST':
        user = request.user
        
        # Saugumas: Patikrinimas ar vartotojas turi teises
        if not user.is_superuser and not getattr(user.profile, 'is_company_admin', False):
            from django.contrib import messages
            messages.error(request, 'Neturite teisių atlikti šio veiksmo.')
            return redirect('home')
            
        user_id = request.POST.get('user_id')
        department_id = request.POST.get('department_id')
        if user_id and department_id:
            target_user = get_object_or_404(User, id=user_id)
            department = get_object_or_404(Department, id=department_id)
            # Ensure both belong to the same company as the current user
            user_company = request.user.profile.company_link
            if department.company == user_company and target_user.profile.company_link == user_company:
                target_user.profile.department = department
                target_user.profile.save()
    return redirect('company_management')

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
def superadmin_download_employee_template(request):
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="darbuotojai_pavyzdys.csv"'},
    )
    # Add BOM for Excel compatibility with UTF-8
    response.write('\ufeff'.encode('utf8'))
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Vardas', 'Pavardė', 'El. paštas', 'Slaptažodis', 'Komandos pavadinimas'])
    writer.writerow(['Jonas', 'Jonaitis', 'jonas.jonaitis@imone.lt', 'slaptazodis123', 'IT Skyrius'])
    writer.writerow(['Petras', 'Petraitis', 'petras.petraitis@imone.lt', 'slaptazodis456', 'Pardavimai'])
    
    return response

@user_passes_test(lambda u: u.is_superuser)
def superadmin_create_company(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            from users.models import Company, Department, Profile
            from django.contrib.auth.models import User
            from django.db import transaction
            import csv
            import io

            try:
                with transaction.atomic():
                    company = Company.objects.create(name=name)
                    employee_file = request.FILES.get('employee_list')
                    
                    if employee_file:
                        file_ext = employee_file.name.split('.')[-1].lower()
                        if file_ext == 'csv':
                            file_data = employee_file.read().decode('utf-8-sig')
                            sniffer = csv.Sniffer()
                            try:
                                dialect = sniffer.sniff(file_data[:1024])
                                csv_data = csv.reader(io.StringIO(file_data), dialect)
                            except csv.Error:
                                if ';' in file_data[:1024]:
                                    csv_data = csv.reader(io.StringIO(file_data), delimiter=';')
                                else:
                                    csv_data = csv.reader(io.StringIO(file_data), delimiter=',')
                                    
                            next(csv_data, None) # Skip header
                            for row in csv_data:
                                if len(row) >= 5:
                                    first_name = row[0].strip()
                                    last_name = row[1].strip()
                                    email = row[2].strip()
                                    password = row[3].strip()
                                    team_name = row[4].strip()
                                    
                                    if not email: continue
                                    
                                    user, created = User.objects.get_or_create(email=email, defaults={
                                        'username': email,
                                        'first_name': first_name,
                                        'last_name': last_name,
                                    })
                                    if created or not user.has_usable_password():
                                        user.set_password(password)
                                        user.save()
                                        
                                    department = None
                                    if team_name:
                                        department, _ = Department.objects.get_or_create(name=team_name, company=company)
                                        
                                    profile, _ = Profile.objects.get_or_create(user=user)
                                    profile.company_link = company
                                    if department:
                                        profile.department = department
                                    profile.save()
                        elif file_ext in ['xlsx', 'xls']:
                            try:
                                import openpyxl
                                wb = openpyxl.load_workbook(employee_file)
                                sheet = wb.active
                                for row in sheet.iter_rows(min_row=2, values_only=True):
                                    if row and len(row) >= 5 and row[2]:
                                        first_name = str(row[0]).strip() if row[0] else ''
                                        last_name = str(row[1]).strip() if row[1] else ''
                                        email = str(row[2]).strip()
                                        password = str(row[3]).strip() if row[3] else ''
                                        team_name = str(row[4]).strip() if row[4] else ''
                                        
                                        user, created = User.objects.get_or_create(email=email, defaults={
                                            'username': email,
                                            'first_name': first_name,
                                            'last_name': last_name,
                                        })
                                        if created or not user.has_usable_password():
                                            user.set_password(password)
                                            user.save()
                                            
                                        department = None
                                        if team_name:
                                            department, _ = Department.objects.get_or_create(name=team_name, company=company)
                                            
                                        profile, _ = Profile.objects.get_or_create(user=user)
                                        profile.company_link = company
                                        if department:
                                            profile.department = department
                                        profile.save()
                            except ImportError:
                                messages.warning(request, f'Įmonė "{name}" sukurta, bet nepavyko apdoroti Excel failo. Instaliuokite "openpyxl".')
                                return redirect('superadmin_companies_list')
                                
                    messages.success(request, f'Įmonė "{name}" sėkmingai sukurta.')
            except Exception as e:
                messages.error(request, f'Įvyko klaida: {str(e)}')
            return redirect('superadmin_companies_list')
    return render(request, 'superadmin/company_create.html')

@user_passes_test(lambda u: u.is_superuser)
def superadmin_company_detail(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    employee_count = company.profile_set.count()
    department_count = company.departments.count()
    employees = Profile.objects.filter(company_link=company).select_related('user', 'department').order_by('-is_company_admin', 'user__first_name')

    context = {
        'company': company,
        'employee_count': employee_count,
        'department_count': department_count,
        'employees': employees,
    }
    return render(request, 'superadmin/company_detail.html', context)

@user_passes_test(lambda u: u.is_superuser)
@require_POST
def superadmin_toggle_company(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    company.is_active = not company.is_active
    company.save()
    status = 'įjungta' if company.is_active else 'išjungta'
    messages.success(request, f'Įmonė "{company.name}" apskaitos būsena pakeista į: {status}.')
    return redirect('superadmin_companies_list')

@user_passes_test(lambda u: u.is_superuser)
@require_POST
def superadmin_delete_company(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    name = company.name
    # Prieš trinant įmonę patikriname, ar reikia išvalyti vartotojus:
    # Company model is linked to Profile. CASCADE delete will delete profiles if models.CASCADE is set.
    # But usually it's models.SET_NULL or CASCADE based on users/models.py logic.
    # In Profile it is models.SET_NULL. Thus users are kept but unlinked.
    # For now we'll just delete the Company object safely.
    company.delete()
    messages.success(request, f'Įmonė "{name}" sėkmingai ištrinta.')
    return redirect('superadmin_companies_list')

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
        # Override parent and manager querysets to target company
        form.fields['parent'].queryset = Department.objects.filter(company=company)
        form.fields['manager'].queryset = User.objects.filter(profile__company_link=company)
        
        if form.is_valid():
            department = form.save(commit=False)
            department.company = company
            department.save()
            # Auto-assign manager to this department
            if department.manager:
                manager_profile = department.manager.profile
                manager_profile.department = department
                manager_profile.save()
            return redirect('superadmin_edit_hierarchy', company_id=company_id)
    else:
        form = DepartmentForm(request.user)
        form.fields['parent'].queryset = Department.objects.filter(company=company)
        form.fields['manager'].queryset = User.objects.filter(profile__company_link=company)

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
    departments = Department.objects.filter(company=company)
    
    context = {
        'company': company,
        'profiles': profiles,
        'departments': departments,
    }
    return render(request, 'superadmin/edit_employees.html', context)

@user_passes_test(lambda u: u.is_superuser)
def superadmin_add_employee(request, company_id):
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        password = request.POST.get('password')
        department_id = request.POST.get('department_id')
        
        company = get_object_or_404(Company, id=company_id)
        department = Department.objects.filter(id=department_id, company=company).first() if department_id else None

        try:
            user = User.objects.get(email=email)
            
            # Update user details if provided
            updated = False
            if first_name:
                user.first_name = first_name
                updated = True
            if last_name:
                user.last_name = last_name
                updated = True
            if password:
                user.set_password(password)
                updated = True
            if updated:
                user.save()

            if hasattr(user, 'profile'):
                if user.profile.company_link and user.profile.company_link != company:
                    messages.error(request, f'Vartotojas {email} jau priklauso kitai įmonei.')
                else:
                    user.profile.company_link = company
                    user.profile.department = department
                    user.profile.save()
                    messages.success(request, f'Vartotojas {email} sėkmingai atnaujintas / pridėtas prie įmonės.')
            else:
                 # If user has no profile, create one
                Profile.objects.create(user=user, company_link=company, department=department)
                messages.success(request, f'Vartotojas {email} sėkmingai pridėtas prie įmonės.')

        except User.DoesNotExist:
            # Create a new user
            username = email.split('@')[0]
            # Handle potential username conflicts
            if User.objects.filter(username=username).exists():
                import uuid
                username = f"{username}_{str(uuid.uuid4())[:8]}"
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password if password else User.objects.make_random_password(),
                first_name=first_name,
                last_name=last_name
            )
            
            # The Profile is usually auto-created by signals, so we retrieve or create it to avoid IntegrityError
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.company_link = company
            profile.department = department
            profile.save()
            
            messages.success(request, f'Naujas vartotojas {email} sėkmingai sukurtas ir pridėtas.')
    
    return redirect('superadmin_edit_employees', company_id=company_id)

@user_passes_test(lambda u: u.is_superuser)
def superadmin_import_employees(request, company_id):
    if request.method == 'POST':
        company = get_object_or_404(Company, id=company_id)
        employee_file = request.FILES.get('employee_list')
        
        if employee_file:
            from django.db import transaction
            import csv
            import io
            
            try:
                with transaction.atomic():
                    file_ext = employee_file.name.split('.')[-1].lower()
                    added_count = 0
                    
                    if file_ext == 'csv':
                        file_data = employee_file.read().decode('utf-8-sig')
                        sniffer = csv.Sniffer()
                        try:
                            dialect = sniffer.sniff(file_data[:1024])
                            csv_data = csv.reader(io.StringIO(file_data), dialect)
                        except csv.Error:
                            if ';' in file_data[:1024]:
                                csv_data = csv.reader(io.StringIO(file_data), delimiter=';')
                            else:
                                csv_data = csv.reader(io.StringIO(file_data), delimiter=',')
                                
                        next(csv_data, None) # Skip header
                        for row in csv_data:
                            if len(row) >= 5:
                                first_name = row[0].strip()
                                last_name = row[1].strip()
                                email = row[2].strip()
                                password = row[3].strip()
                                team_name = row[4].strip()
                                
                                if not email: continue
                                
                                user, created = User.objects.get_or_create(email=email, defaults={
                                    'username': email,
                                    'first_name': first_name,
                                    'last_name': last_name,
                                })
                                if created or not user.has_usable_password():
                                    user.set_password(password)
                                    user.save()
                                    
                                department = None
                                if team_name:
                                    department, _ = Department.objects.get_or_create(name=team_name, company=company)
                                    
                                profile, _ = Profile.objects.get_or_create(user=user)
                                profile.company_link = company
                                if department:
                                    profile.department = department
                                profile.save()
                                added_count += 1
                                
                    elif file_ext in ['xlsx', 'xls']:
                        try:
                            import openpyxl
                            wb = openpyxl.load_workbook(employee_file)
                            sheet = wb.active
                            for row in sheet.iter_rows(min_row=2, values_only=True):
                                if row and len(row) >= 5 and row[2]:
                                    first_name = str(row[0]).strip() if row[0] else ''
                                    last_name = str(row[1]).strip() if row[1] else ''
                                    email = str(row[2]).strip()
                                    password = str(row[3]).strip() if row[3] else ''
                                    team_name = str(row[4]).strip() if row[4] else ''
                                    
                                    user, created = User.objects.get_or_create(email=email, defaults={
                                        'username': email,
                                        'first_name': first_name,
                                        'last_name': last_name,
                                    })
                                    if created or not user.has_usable_password():
                                        user.set_password(password)
                                        user.save()
                                        
                                    department = None
                                    if team_name:
                                        department, _ = Department.objects.get_or_create(name=team_name, company=company)
                                        
                                    profile, _ = Profile.objects.get_or_create(user=user)
                                    profile.company_link = company
                                    if department:
                                        profile.department = department
                                    profile.save()
                                    added_count += 1
                        except ImportError:
                            messages.warning(request, 'Nepavyko apdoroti Excel failo. Instaliuokite "openpyxl".')
                            return redirect('superadmin_edit_employees', company_id=company_id)
                            
                    messages.success(request, f'Sėkmingai importuota / atnaujinta {added_count} darbuotojų iš sąrašo.')
            except Exception as e:
                messages.error(request, f'Klaida apdorojant failą: {str(e)}')
        else:
            messages.error(request, 'Nepasirinktas joks failas.')
            
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
def superadmin_edit_department(request, company_id, department_id):
    company = get_object_or_404(Company, id=company_id)
    department = get_object_or_404(Department, id=department_id, company=company)
    
    if request.method == 'POST':
        form = DepartmentForm(request.user, request.POST, instance=department)
        # Override parent and manager querysets to target company's departments, excluding self to prevent loop
        form.fields['parent'].queryset = Department.objects.filter(company=company).exclude(id=department.id)
        form.fields['manager'].queryset = User.objects.filter(profile__company_link=company)
        
        if form.is_valid():
            dept = form.save()
            if dept.manager:
                manager_profile = dept.manager.profile
                manager_profile.department = dept
                manager_profile.save()
            messages.success(request, f'Departamentas "{dept.name}" sėkmingai atnaujintas.')
            return redirect('superadmin_edit_hierarchy', company_id=company_id)
    else:
        form = DepartmentForm(request.user, instance=department)
        form.fields['parent'].queryset = Department.objects.filter(company=company).exclude(id=department.id)
        form.fields['manager'].queryset = User.objects.filter(profile__company_link=company)

    context = {
        'company': company,
        'department': department,
        'form': form,
    }
    return render(request, 'superadmin/edit_department.html', context)

@user_passes_test(lambda u: u.is_superuser)
def superadmin_toggle_admin(request, company_id, user_id):
    if request.method == 'POST':
        company = get_object_or_404(Company, id=company_id)
        target_user = get_object_or_404(User, id=user_id)
        if hasattr(target_user, 'profile') and target_user.profile.company_link == company:
            target_user.profile.is_company_admin = not target_user.profile.is_company_admin
            target_user.profile.save()
            status = 'priskirtas' if target_user.profile.is_company_admin else 'pašalintas iš'
            messages.success(request, f'{target_user.get_full_name()} {status} administratorių.')
    return redirect('superadmin_company_detail', company_id=company_id)

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
        
        # Remove the impersonator ID from the session safely
        request.session.pop('impersonator_id', None)
        
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
        'is_company_active': is_company_active(request.user)
    })

@login_required
def create_questionnaire(request):
    from .models import Questionnaire, Trait
    if not is_company_active(request.user):
        messages.error(request, 'Jūsų įmonė yra išjungta. Veiksmas negalimas.')
        return redirect('questionnaires_list')
        
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
    
    if not is_company_active(request.user):
        messages.error(request, 'Jūsų įmonė yra išjungta. Veiksmas negalimas.')
        return redirect('questionnaires_list')
        
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
        project_name=questionnaire.title,
        questionnaire=questionnaire,
        comment=f"Prašau užpildyti klausimyną: {questionnaire.title}",
        due_date=date.today()
    )
    
    messages.success(request, f'Klausimynas "{questionnaire.title}" sėkmingai išsiųstas kolegai {requested_to.first_name} {requested_to.last_name}.')
    return redirect('questionnaires_list')

@login_required
def edit_questionnaire(request, questionnaire_id):
    from .models import Questionnaire, Trait # Added import here for edit_questionnaire
    questionnaire = get_object_or_404(Questionnaire, id=questionnaire_id, created_by=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        trait_ids = request.POST.getlist('trait_ids')
        custom_traits = request.POST.getlist('custom_traits')
        
        if not title:
            messages.error(request, 'Klausimyno pavadinimas yra privalomas.')
            return redirect('questionnaires_list')
            
        questionnaire.title = title
        questionnaire.save()
        
        # Clear existing traits
        questionnaire.traits.clear()
        
        # Add selected existing traits
        for trait_id in trait_ids:
            try:
                trait = Trait.objects.get(id=trait_id)
                questionnaire.traits.add(trait)
            except Trait.DoesNotExist:
                continue
                
        # Add new custom traits
        for trait_name in custom_traits:
            name = trait_name.strip()
            if name:
                trait, created = Trait.objects.get_or_create(
                    name=name,
                    defaults={'created_by': request.user}
                )
                questionnaire.traits.add(trait)
                
        messages.success(request, 'Klausimynas sėkmingai atnaujintas.')
        return redirect('questionnaires_list')
        
    messages.error(request, 'Klaida atnaujinant klausimyną.')
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
    ).select_related('requested_to')
    
    feedbacks = Feedback.objects.filter(feedback_request__in=feedback_requests)
    
    overall_avg_rating = feedbacks.aggregate(Avg('rating'))['rating__avg'] or 0
    received_feedback_count = feedbacks.count()
    
    from .models import TraitRating
    from collections import defaultdict

    traits = questionnaire.traits.all()
    trait_ratings = TraitRating.objects.filter(feedback__in=feedbacks)
    
    competencies = []
    
    # Pre-fetch trait ratings per date for chart
    trait_ratings_by_date = defaultdict(lambda: defaultdict(list))
    for tr in trait_ratings.select_related('feedback__feedback_request'):
        d = tr.feedback.feedback_request.created_at.date()
        trait_ratings_by_date[tr.trait_id][d].append(tr.rating)

    for trait in traits:
        # Average score for this trait
        avg = trait_ratings.filter(trait=trait).aggregate(Avg('rating'))['rating__avg'] or 0
        competencies.append({
            'name': trait.name,
            'score': round(avg, 2)
        })

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
        avg_rating=Avg('rating')
    ).order_by('date')

    chart_labels = [fb['date'].strftime('%Y-%m-%d') if fb['date'] else 'Data nežinoma' for fb in chronological_feedbacks]
    
    chart_datasets = [
        {'label': 'Bendras', 'data': [round(fb['avg_rating'], 2) for fb in chronological_feedbacks], 'borderColor': '#8B5CF6', 'tension': 0.3},
    ]
    
    colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#6366F1', '#EC4899', '#14B8A6', '#F43F5E']
    
    for i, trait in enumerate(traits):
        data = []
        for fb_dict in chronological_feedbacks:
            d = fb_dict['date']
            # if d is None, fallback
            ratings = trait_ratings_by_date[trait.id].get(d, [])
            avg = sum(ratings) / len(ratings) if ratings else 0.0
            data.append(round(avg, 2))
            
        chart_datasets.append({
            'label': trait.name,
            'data': data,
            'borderColor': colors[i % len(colors)],
            'tension': 0.3,
            'hidden': True
        })

    chart_data = {
        'labels': chart_labels,
        'datasets': chart_datasets
    }

    context = {
        'questionnaire': questionnaire,
        'overall_avg_rating': round(overall_avg_rating, 2),
        'received_feedback_count': received_feedback_count,
        'competencies': competencies,
        'all_keywords': all_keywords,
        'strengths': strengths,
        'improvements': improvements,
        'chart_data_json': json.dumps(chart_data),
    }

    
    return render(request, 'questionnaires/statistics.html', context)


# ==========================================
# SUPERUSERS MANAGEMENT (SUPERADMIN)
# ==========================================

@user_passes_test(lambda u: u.is_superuser)
def superadmin_superusers_list(request):
    superusers = User.objects.filter(is_superuser=True).order_by('-date_joined')
    return render(request, 'superadmin/superusers_list.html', {'superusers': superusers})

@user_passes_test(lambda u: u.is_superuser)
def superadmin_create_superuser(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, 'El. paštas ir slaptažodis yra privalomi.')
            return render(request, 'superadmin/superuser_form.html')

        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            messages.error(request, 'Vartotojas su tokiu el. paštu jau egzistuoja.')
            return render(request, 'superadmin/superuser_form.html')

        user = User.objects.create_superuser(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        messages.success(request, f'Supervartotojas {email} sėkmingai sukurtas.')
        return redirect('superadmin_superusers_list')

    return render(request, 'superadmin/superuser_form.html')

@user_passes_test(lambda u: u.is_superuser)
def superadmin_edit_superuser(request, user_id):
    superuser = get_object_or_404(User, id=user_id, is_superuser=True)
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')

        superuser.first_name = first_name
        superuser.last_name = last_name
        
        if password:
            superuser.set_password(password)
            
        superuser.save()
        messages.success(request, f'Supervartotojo {superuser.email} duomenys atnaujinti.')
        return redirect('superadmin_superusers_list')

    return render(request, 'superadmin/superuser_form.html', {'superuser': superuser})

@user_passes_test(lambda u: u.is_superuser)
def superadmin_delete_superuser(request, user_id):
    if request.method == 'POST':
        superuser = get_object_or_404(User, id=user_id, is_superuser=True)
        if superuser == request.user:
            messages.error(request, 'Negalite ištrinti patys savęs.')
        else:
            superuser.delete()
            messages.success(request, 'Supervartotojas sėkmingai ištrintas.')
    return redirect('superadmin_superusers_list')

@user_passes_test(lambda u: u.is_superuser)
def superadmin_users_list(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        company_id = request.POST.get('company_id')
        
        if user_id and company_id:
            target_user = get_object_or_404(User, id=user_id, is_superuser=False)
            
            if company_id == 'none':
                target_user.profile.company_link = None
            else:
                company = get_object_or_404(Company, id=company_id)
                target_user.profile.company_link = company
                
            target_user.profile.save()
            messages.success(request, f'Vartotojo {target_user.email} įmonė atnaujinta.')
            
        return redirect('superadmin_users_list')

    sys_users = User.objects.filter(is_superuser=False).select_related('profile', 'profile__company_link').order_by('-date_joined')
    companies = Company.objects.all().order_by('name')
    
    context = {
        'users': sys_users,
        'companies': companies
    }
    
    return render(request, 'superadmin/users_list.html', context)

