from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm, FeedbackForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .models import FeedbackRequest, Feedback
from users.models import Profile
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db import OperationalError
from django.views.decorators.http import require_POST
import json
import google.generativeai as genai
from django.conf import settings
from django.db.models import Avg
import logging

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
        company_name = request.user.profile.company
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
            company = form.cleaned_data.get('company')
            Profile.objects.create(user=user, company=company)
            login(request, user)
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
    try:
        user_company = user.profile.company
        if user_company:
            team_members = User.objects.filter(profile__company__iexact=user_company).exclude(id=user.id)
        else:
            team_members = User.objects.exclude(id=user.id)
        data = [{'id': member.id, 'name': f'{member.first_name} {member.last_name}'} for member in team_members]
        return JsonResponse(data, safe=False)
    except (Profile.DoesNotExist, OperationalError):
        team_members = User.objects.exclude(id=user.id)
        data = [{'id': member.id, 'name': f'{member.first_name} {member.last_name}'} for member in team_members]
        return JsonResponse(data, safe=False)

@login_required
def request_feedback(request):
    if request.method == 'POST':
        requester = request.user
        requested_to_id = request.POST.get('requested_to')
        project_name = request.POST.get('project_name')
        due_date = request.POST.get('due_date')
        
        requested_to = get_object_or_404(User, id=requested_to_id)
        
        FeedbackRequest.objects.create(
            requester=requester,
            requested_to=requested_to,
            project_name=project_name,
            due_date=due_date
        )
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'errors': 'Invalid request method'})

@login_required
def fill_feedback(request, request_id):
    feedback_request = get_object_or_404(FeedbackRequest, id=request_id, requested_to=request.user)
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
    try:
        user_company = user.profile.company
        if user_company:
            team_members_qs = User.objects.filter(profile__company__iexact=user_company)
        else:
            team_members_qs = User.objects.all()
    except (Profile.DoesNotExist, OperationalError):
        team_members_qs = User.objects.all()

    # Enhance team member data with individual average ratings
    team_members = []
    for member in team_members_qs:
        avg_rating = Feedback.objects.filter(feedback_request__requested_to=member, feedback_request__status='completed').aggregate(Avg('rating'))['rating__avg']
        member.average_rating = round(avg_rating, 1) if avg_rating else 0
        team_members.append(member)

    # Calculate overall team statistics
    pending_feedback_count = FeedbackRequest.objects.filter(requested_to__in=team_members_qs, status='pending').count()
    overall_avg_rating = Feedback.objects.filter(feedback_request__requested_to__in=team_members_qs, feedback_request__status='completed').aggregate(Avg('rating'))['rating__avg']
    
    context = {
        'team_members': team_members,
        'pending_feedback_count': pending_feedback_count,
        'overall_avg_rating': round(overall_avg_rating, 1) if overall_avg_rating else 0,
    }
    return render(request, 'team_members.html', context)

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



import traceback

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

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')

        prompt = f"""
        Apibendrink šį grįžtamąjį ryšį apie komandos narį, vardu {colleague_name}.

        **Kontekstas:**
        Tai yra kolegos vertinimas. Prašau suformuluoti konstruktyvų, profesionalų atsiliepimą apie {colleague_name}, srityse kurios įvertintos žemiau 7 gali duoti lengvos kritikos.
        Tekstas turi būti parašytas lietuvių kalba.

        **Duomenys:**
        - **Kompetencijų įvertinimai (1-10, kur 10 yra puikiai):**
          - Bendras įvertinimas: {ratings.get('rating')}
          - Komandinis Darbas: {ratings.get('teamwork')}
          - Komunikacija: {ratings.get('communication')}
          - Iniciatyvumas: {ratings.get('initiative')}
          - Techninės Žinios: {ratings.get('technical_skills')}
          - Problemų Sprendimas: {ratings.get('problem_solving')}
        
        - **Raktiniai žodžiai:** {keywords}
        
        - **Komentarai:** {comments}

        - **Esamas išsamus atsiliepimas (jei yra, papildyk jį):** {existing_feedback}

        **Užduotis:**
        Remdamasis pateiktais duomenimis, sugeneruok sklandų ir išsamų atsiliepimo tekstą apie {colleague_name}. 
        - Pradėk nuo bendro teigiamo įspūdžio (jei įvertinimai geri).
        - Išskirk 2-3 stipriąsias puses, pagrįsdamas jas raktiniais žodžiais ar aukštais įvertinimais.
        - Atsižvelk į laisvos formos komentarus.
        - Jei yra žemų įvertinimų ar neigiamų raktinių žodžių, pasiūlyk 1-2 tobulintinas sritis. Formuluok pasiūlymus kaip galimybes augti, o ne kaip kritiką.
        - Apibendrink atsiliepimą pozityvia nata.
        - Nenaudok Markdown formatavimo.
        """

        response = model.generate_content(prompt)
        
        return JsonResponse({'generated_feedback': response.text})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def results(request):
    user = request.user
    
    # Gauti visus užbaigtus atsiliepimus vartotojui
    completed_feedback = Feedback.objects.filter(feedback_request__requested_to=user, feedback_request__status='completed')
    
    # Apskaičiuoti bendrą vidutinį įvertinimą
    overall_avg_rating = completed_feedback.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Surinkti visus raktinius žodžius
    all_keywords = []
    for feedback in completed_feedback:
        keywords = [kw.strip() for kw in feedback.keywords.split(',') if kw.strip()]
        all_keywords.extend(keywords)

    # Surinkti kokybinius atsiliepimus
    qualitative_feedback = [f.feedback for f in completed_feedback]

    # Apskaičiuoti kompetencijų vidurkius
    competencies = [
        {'name': 'Komandinis Darbas', 'score': round(completed_feedback.aggregate(Avg('teamwork_rating'))['teamwork_rating__avg'] or 0, 1)},
        {'name': 'Komunikacija', 'score': round(completed_feedback.aggregate(Avg('communication_rating'))['communication_rating__avg'] or 0, 1)},
        {'name': 'Iniciatyvumas', 'score': round(completed_feedback.aggregate(Avg('initiative_rating'))['initiative_rating__avg'] or 0, 1)},
        {'name': 'Techninės Žinios', 'score': round(completed_feedback.aggregate(Avg('technical_skills_rating'))['technical_skills_rating__avg'] or 0, 1)},
        {'name': 'Problemų Sprendimas', 'score': round(completed_feedback.aggregate(Avg('problem_solving_rating'))['problem_solving_rating__avg'] or 0, 1)},
    ]

    context = {
        'overall_avg_rating': round(overall_avg_rating, 1),
        'received_feedback_count': completed_feedback.count(),
        'all_keywords': list(set(all_keywords))[:7], # Paimti unikalius raktinius žodžius
        'competencies': competencies,
        'strengths': qualitative_feedback[:3], # Laikinai priskiriame pirmuosius atsiliepimus kaip stiprybes
        'improvements': qualitative_feedback[3:5], # Laikinai priskiriame kitus kaip tobulintinas sritis
        'company_name': request.user.profile.company if hasattr(request.user, 'profile') else '',
    }
    
    return render(request, 'results.html', context)
