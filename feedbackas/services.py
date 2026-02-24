import google.generativeai as genai
from django.conf import settings
from django.db.models import Avg
from .models import Feedback, FeedbackRequest
from django.contrib.auth.models import User

class FeedbackGenerator:
    @staticmethod
    def generate(ratings, keywords, comments, existing_feedback, colleague_name):
        """
        Generuoja grįžtamąjį ryšį naudojant Google Gemini AI.
        """
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-pro')
        model = genai.GenerativeModel(model_name)

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

        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            # Fallback for unsupported models or API versions
            try:
                fallback_model = genai.GenerativeModel("gemini-pro")
                response = fallback_model.generate_content(prompt)
                return response.text
            except Exception as e2:
                print(f"Fallback generation also failed: {e2}")
                raise e

    @staticmethod
    def extract_strengths_weaknesses(feedback_text, comments_text):
        """
        Iš tekstinio atsiliepimo išveda stiprybes ir tobulintinas sritis JSON formatu.
        """
        if not feedback_text and not comments_text:
            return {"strengths": [], "improvements": []}
            
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-pro')
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        Išanalizuok žemiau pateiktą darbuotojo atsiliepimą ir išskirk dvi kategorijas:
        1. Stiprybės (gerosios savybės, ką darbuotojas daro gerai)
        2. Tobulintinos sritys (kas buvo paminėta kaip silpnybė arba kur galima tobulėti)

        Atsakymą pateik GRIEŽTAI TIK JSON formatu be jokio papildomo teksto, Markdown blokų ar paaiškinimų.
        Kiekvienas punktas turi būti suformuluotas trumpai (1-2 sakiniai).
        
        Pavyzdys:
        {{
            "strengths": ["Puikiai sprendžia technines problemas.", "Greitai mokosi naujų technologijų."],
            "improvements": ["Galėtų dažniau imtis iniciatyvos komandos susirinkimuose.", "Vertėtų tobulinti viešo kalbėjimo įgūdžius."]
        }}

        Atsiliepimas:
        {feedback_text}
        
        Papildomas komentaras:
        {comments_text}
        """
        
        try:
            response = model.generate_content(prompt)
        except Exception:
            try:
                fallback_model = genai.GenerativeModel("gemini-pro")
                response = fallback_model.generate_content(prompt)
            except Exception as e:
                print(f"Failed to extract traits on fallback: {e}")
                return {"strengths": [], "improvements": []}
                
        try:
            # Bandome išvalyti Markdown kodą iš grąžinto atsakymo, jei AI vis tik jį pridėtų
            cleaned_text = response.text.replace('```json', '').replace('```', '').strip()
            import json
            data = json.loads(cleaned_text)
            return {
                "strengths": data.get("strengths", []),
                "improvements": data.get("improvements", [])
            }
        except Exception as e:
            print(f"Failed to extract traits: {e}")
            return {"strengths": [], "improvements": []}

class FeedbackAnalytics:
    @staticmethod
    def get_user_stats(user, period='all'):
        """
        Apskaičiuoja vartotojo atsiliepimų statistiką ir kompetencijų vidurkius.
        """
        from django.utils import timezone
        import datetime
        
        filters = {
            'feedback_request__requester': user,
            'feedback_request__status': 'completed'
        }
        
        now = timezone.now()
        if period == 'month':
            filters['feedback_request__created_at__gte'] = now - datetime.timedelta(days=30)
        elif period == 'quarter':
            filters['feedback_request__created_at__gte'] = now - datetime.timedelta(days=90)
        elif period == 'year':
            filters['feedback_request__created_at__gte'] = now - datetime.timedelta(days=365)
            
        completed_feedback = Feedback.objects.filter(**filters)
        completed_feedback_count = completed_feedback.count()
        
        # Participation Rate
        total_requests_filters = {'requester': user}
        if period == 'month':
            total_requests_filters['created_at__gte'] = now - datetime.timedelta(days=30)
        elif period == 'quarter':
            total_requests_filters['created_at__gte'] = now - datetime.timedelta(days=90)
        elif period == 'year':
            total_requests_filters['created_at__gte'] = now - datetime.timedelta(days=365)
        
        total_requests = FeedbackRequest.objects.filter(**total_requests_filters).count()
        participation_rate = 0
        if total_requests > 0:
            participation_rate = int((completed_feedback_count / total_requests) * 100)
            
        overall_avg_rating = completed_feedback.aggregate(Avg('rating'))['rating__avg'] or 0
        
        # Top % In Company
        top_percentile = '--'
        if hasattr(user, 'profile') and user.profile.company_link:
            company = user.profile.company_link
            company_users = User.objects.filter(profile__company_link=company)
            
            user_scores = []
            for u in company_users:
                u_filters = {
                    'feedback_request__requester': u,
                    'feedback_request__status': 'completed'
                }
                if period == 'month':
                    u_filters['feedback_request__created_at__gte'] = now - datetime.timedelta(days=30)
                elif period == 'quarter':
                    u_filters['feedback_request__created_at__gte'] = now - datetime.timedelta(days=90)
                elif period == 'year':
                    u_filters['feedback_request__created_at__gte'] = now - datetime.timedelta(days=365)
                    
                u_avg = Feedback.objects.filter(**u_filters).aggregate(Avg('rating'))['rating__avg'] or 0
                if u_avg > 0:
                    user_scores.append(u_avg)
                    
            if user_scores and overall_avg_rating > 0:
                user_scores.sort(reverse=True)
                if overall_avg_rating in user_scores:
                    rank = user_scores.index(overall_avg_rating) + 1
                    percentile_calc = int((rank / len(user_scores)) * 100)
                    top_percentile = percentile_calc if percentile_calc > 0 else 1
        
        all_keywords = []
        all_strengths = []
        all_improvements = []
        
        for feedback in completed_feedback:
            keywords = [kw.strip() for kw in feedback.keywords.split(',') if kw.strip()]
            all_keywords.extend(keywords)
            
            # Sumuojame AI išskirtas savybes
            if isinstance(feedback.extracted_strengths, list):
                all_strengths.extend(feedback.extracted_strengths)
            if isinstance(feedback.extracted_improvements, list):
                all_improvements.extend(feedback.extracted_improvements)

        competency_averages = completed_feedback.aggregate(
            teamwork=Avg('teamwork_rating'),
            communication=Avg('communication_rating'),
            initiative=Avg('initiative_rating'),
            technical_skills=Avg('technical_skills_rating'),
            problem_solving=Avg('problem_solving_rating')
        )
        competencies = [
            {'name': 'Komandinis Darbas', 'score': round(competency_averages.get('teamwork') or 0, 2)},
            {'name': 'Komunikacija', 'score': round(competency_averages.get('communication') or 0, 2)},
            {'name': 'Iniciatyvumas', 'score': round(competency_averages.get('initiative') or 0, 2)},
            {'name': 'Techninės Žinios', 'score': round(competency_averages.get('technical_skills') or 0, 2)},
            {'name': 'Problemų Sprendimas', 'score': round(competency_averages.get('problem_solving') or 0, 2)},
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
            if competency['score'] < 7:
                recommended_trainings.append({
                    'competency': competency['name'],
                    'training': training_map.get(competency['name'], 'Bendrieji tobulinimosi kursai')
                })
        
        return {
            'overall_avg_rating': round(overall_avg_rating, 2),
            'received_feedback_count': completed_feedback_count,
            'participation_rate': participation_rate,
            'top_percentile': top_percentile,
            'all_keywords': list(set(all_keywords))[:7],
            'competencies': competencies,
            'strengths': all_strengths[:5],
            'improvements': all_improvements[:5],
            'recommended_trainings': recommended_trainings,
        }