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
import google.generativeai as genai
from django.conf import settings
from django.db.models import Avg
from django.db import models
import logging
from datetime import date


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
        user_company = user.profile.company
        if user_company:
            team_members_qs = User.objects.filter(profile__company__iexact=user_company).exclude(id=user.id)
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
        user_company = user.profile.company
        if user_company:
            # Filtruojame pagal įmonę ir atmetame patį vartotoją
            team_members_qs = User.objects.filter(profile__company__iexact=user_company).exclude(id=user.id)
        else:
            # Jei vartotojas neturi įmonės, rodome visus vartotojus be įmonės
            team_members_qs = User.objects.filter(Q(profile__company__isnull=True) | Q(profile__company='')).exclude(id=user.id)
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

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')

        prompt = f"""
        Veik kaip konkretus, kolegiškas komandos narys, būk empatiškas ir teik konstruktyvią kritiką.
        Eik iš kato prie esmės, nereikia jokių įžangų ir atsisveikinimų.
        Tavo užduotis - sugeneruoti kokybišką, duomenimis pagrįstą grįžtamąjį ryšį kolegai {colleague_name}.
        
        **SVARBU: Vertinimo sistema (Kontekstas):**
        Mes nenaudojame standartinių balų. Mes naudojame augimo skalę (1-4):
        - **1 = 🌱 Learning (Mokosi / Reikia pagalbos):** Tai nėra "blogai", tai reiškia, kad čia reikia skirti dėmesio, mokytis ir tobulėti.
        - **2 = 🏃 Doing (Daro / Atitinka lūkesčius):** Tai solidus pagrindas, kolega susitvarko.
        - **3 = 🚀 Driving (Varo / Viršija lūkesčius):** Kolega rodo iniciatyvą ir tempia komandą.
        - **4 = ⭐️ Role Model (Pavyzdys kitiems):** Tai superžvaigždės lygis, kiti turi mokytis iš jo.
        
        **JOKIO FORMATAVIMO (NO MARKDOWN):**    
        - Griežtai **NENAUDOK** jokių žvaigždučių (`**` ar `*`), paryškinimų, punktų (bullet points) ar antraščių.    
        - **NERAŠYK** etikečių kaip "Situacija:", "Elgesys:", "Poveikis:", "Lygis:".    
        - Tekstas turi būti paprastas, suskirstytas tik į pastraipas (paragraphs), glaustas, konkretus. Tai turi atrodyti kaip paprastas el. laiškas ar žinutė nuo kolegos.
        - Maksimalus ilgis 160-180 žodžių.

        
        Naudok Situation-Behavior-Impact logiką, bet integruok ją į sakinius natūraliai.
 
        
        **Duomenys:**
        - **Kompetencijų lygiai (1-4):**
        - Bendras: {ratings.get('rating')}
        - Komandinis Darbas: {ratings.get('teamwork')}
        - Komunikacija: {ratings.get('communication')}
        - Iniciatyvumas: {ratings.get('initiative')}
        - Techninės Žinios: {ratings.get('technical_skills')}
        - Problemų Sprendimas: {ratings.get('problem_solving')}
        
        - **Raktiniai žodžiai:** {keywords}
        - **Komentarai:** {comments}
        - **Papildomas kontekstas:** {existing_feedback}
        
        **Generavimo Instrukcija:**
        Parašyk rišlų atsiliepimą lietuvių kalba, skirtą {colleague_name}:
        
        1. **Stiprybės (Lygiai 3-4 "Varo" ir "Pavyzdys"):**
        Jei yra sričių su įvertinimais 3 arba 4, paminėk jas kaip pavyzdines. Naudok tokias frazes kaip "Šioje srityje esi pavyzdys kitiems", "Čia tu tikrai varai į priekį". Konkrečiai įvardink, kokį teigiamą poveikį (Impact) tai daro.
        
        2. **Stabilumas (Lygis 2 "Daro"):**
        Jei sritis įvertinta 2, paminėk tai kaip stabilią, patikimą veiklą, kuri atitinka lūkesčius.
        
        3. **Augimo zonos (Lygis 1 "Mokosi"):**
        Jei yra sričių su įvertinimu 1 (arba 1.x), tai yra vieta SBI konstruktyvumui.
        NEKRITIKUOK asmenybės. Formuluok tai kaip galimybę mokytis: "Matau galimybę augti...", "Čia dar galime pasitempti...".
        Būtinai paaiškink Situaciją ir Elgesį, kuris lėmė tokį vertinimą, ir pasiūlyk, kaip pasiekti "Daro" lygį.
        
        4. **Komentarų integracija:**
        Natūraliai įpink pateiktus komentarus ir raktinius žodžius į tekstą, kad jie neskambėtų kaip atskiras sąrašas.
        
        Tekstas turi būti motyvuojantis, profesionalus ir aiškus. Nenaudok Markdown formatavimo.
        """

        response = model.generate_content(prompt)
        
        return JsonResponse({'generated_feedback': response.text})

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
    
    # Gauti visus užbaigtus atsiliepimus vartotojui
    completed_feedback = Feedback.objects.filter(feedback_request__requester=user, feedback_request__status='completed')
    
    # Apskaičiuoti bendrą vidutinį įvertinimą
    overall_avg_rating = completed_feedback.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Surinkti visus raktinius žodžius
    all_keywords = []
    for feedback in completed_feedback:
        keywords = [kw.strip() for kw in feedback.keywords.split(',') if kw.strip()]
        all_keywords.extend(keywords)

    # Surinkti kokybinius atsiliepimus
    qualitative_feedback = [f.feedback for f in completed_feedback]

    # Apskaičiuoti kompetencijų vidurkius viena užklausa
    competency_averages = completed_feedback.aggregate(
        teamwork=Avg('teamwork_rating'),
        communication=Avg('communication_rating'),
        initiative=Avg('initiative_rating'),
        technical_skills=Avg('technical_skills_rating'),
        problem_solving=Avg('problem_solving_rating')
    )
    competencies = [
        {'name': 'Komandinis Darbas', 'score': round(competency_averages.get('teamwork') or 0, 1)},
        {'name': 'Komunikacija', 'score': round(competency_averages.get('communication') or 0, 1)},
        {'name': 'Iniciatyvumas', 'score': round(competency_averages.get('initiative') or 0, 1)},
        {'name': 'Techninės Žinios', 'score': round(competency_averages.get('technical_skills') or 0, 1)},
        {'name': 'Problemų Sprendimas', 'score': round(competency_averages.get('problem_solving') or 0, 1)},
    ]

    training_map = {
        'Komandinis Darbas': 'Mokymai apie efektyvų komandinį darbą',
        'Komunikacija': 'Viešojo kalbėjimo ir komunikacijos įgūdžių mokymai',
        'Iniciatyvumas': 'Proaktyvumo ir iniciatyvumo skatinimo seminaras',
        'Techninės Žinios': 'Specializuoti techniniai kursai pagal Jūsų sritį',
        'Problemų Sprendimas': 'Kritinio mąstymo ir problemų sprendimo dirbtuvės',
    }
    
    recommended_trainings = []
    for competency in competencies:
        if competency['score'] < 7: # Naudojame 7 kaip ribą, kaip ir AI raginime
            recommended_trainings.append({
                'competency': competency['name'],
                'training': training_map.get(competency['name'], 'Bendrieji tobulinimosi kursai')
            })

    context = {
        'overall_avg_rating': round(overall_avg_rating, 1),
        'received_feedback_count': completed_feedback.count(),
        'all_keywords': list(set(all_keywords))[:7], # Paimti unikalius raktinius žodžius
        'competencies': competencies,
        'strengths': qualitative_feedback[:3], # Laikinai priskiriame pirmuosius atsiliepimus kaip stiprybes
        'improvements': qualitative_feedback[3:5], # Laikinai priskiriame kitus kaip tobulintinas sritis
        'recommended_trainings': recommended_trainings,
        'company_name': request.user.profile.company if hasattr(request.user, 'profile') else '',
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
