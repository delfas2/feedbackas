import google.generativeai as genai
from django.conf import settings
from django.db.models import Avg
from .models import Feedback

class FeedbackGenerator:
    @staticmethod
    def generate(ratings, keywords, comments, existing_feedback, colleague_name):
        """
        Generuoja grįžtamąjį ryšį naudojant Google Gemini AI.
        """
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-flash'))

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
        return response.text

class FeedbackAnalytics:
    @staticmethod
    def get_user_stats(user):
        """
        Apskaičiuoja vartotojo atsiliepimų statistiką ir kompetencijų vidurkius.
        """
        completed_feedback = Feedback.objects.filter(feedback_request__requester=user, feedback_request__status='completed')
        
        overall_avg_rating = completed_feedback.aggregate(Avg('rating'))['rating__avg'] or 0
        
        all_keywords = []
        for feedback in completed_feedback:
            keywords = [kw.strip() for kw in feedback.keywords.split(',') if kw.strip()]
            all_keywords.extend(keywords)

        qualitative_feedback = [f.feedback for f in completed_feedback]

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
            'received_feedback_count': completed_feedback.count(),
            'all_keywords': list(set(all_keywords))[:7],
            'competencies': competencies,
            'strengths': qualitative_feedback[:3],
            'improvements': qualitative_feedback[3:5],
            'recommended_trainings': recommended_trainings,
        }