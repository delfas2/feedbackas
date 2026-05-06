import requests
import json
from django.conf import settings
from decimal import Decimal
from feedbackas.models import AIUsageLog

class OpenRouterService:
    @staticmethod
    def _call_openrouter(prompt, user=None, company=None, request_type='general'):
        """
        Siunčia užklausą į OpenRouter API ir grąžina atsakymą bei rinka išlaidas.
        """
        api_key = settings.OPENROUTER_API_KEY
        model = getattr(settings, 'OPENROUTER_MODEL', 'google/gemma-3-27b-it:free')

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }

        payload = {
            'model': model,
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 1024,
        }

        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        data = response.json()
        
        # Sukuriame loginį įrašą
        if user or company:
            usage = data.get('usage', {})
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            # OpenRouter dažniausiai grąžina 'cost', bet kai kurie modeliai/atsakymai gali turėti 'total_cost'
            total_cost = usage.get('cost') or usage.get('total_cost', 0.0)
            
            AIUsageLog.objects.create(
                user=user,
                company=company,
                request_type=request_type,
                model_name=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_cost=Decimal(str(total_cost)),
                raw_response=data
            )
            
        return data['choices'][0]['message']['content']

    @staticmethod
    def generate(ratings, keywords, comments, existing_feedback, colleague_name, user=None, company=None):
        """
        Generuoja grįžtamąjį ryšį naudojant OpenRouter API.
        Prieš siunčiant, tikrasis vardas pakeičiamas žyme privatumui užtikrinti.
        """
        placeholder = "[VARDAS]"
        safe_comments = comments.replace(colleague_name, placeholder) if comments else comments
        safe_existing_feedback = existing_feedback.replace(colleague_name, placeholder) if existing_feedback else existing_feedback
        prompt = f"""
        Veik kaip konkretus, kolegiškas komandos narys, būk empatiškas ir teik konstruktyvią kritiką.
        Eik iš kato prie esmės, nereikia jokių įžangų ir atsisveikinimų.
        Tavo užduotis - sugeneruoti kokybišką, duomenimis pagrįstą grįžtamąjį ryšį kolegai, kurį tekste vadink tik žyme {placeholder}.
        **SVARBU dėl vardo:**
        Visada naudok tik žymę {placeholder} vietoj vardo. Niekada nenaudok tikrojo vardo (jei jį žinai). 
        Nekeisk ir nelinksniuok šios žymės – naudok ją tiksliai tokią, kokia ji yra.
        Tekstas turi būti parašytas taisyklinga lietuvių kalba, be jokių gramatinių klaidų, ir turi būti lengvai skaitomas bei suprantamas.

        **SVARBU: Vertinimo sistema (Kontekstas):**
        Mes nenaudojame standartinių balų. Mes naudojame augimo skalę (1-4):
        - **1 = 🌱 Mokosi (Mokosi / Reikia pagalbos):** Tai nėra "blogai", tai reiškia, kad čia reikia skirti dėmesio, mokytis ir tobulėti.
        - **2 = 🏃 Daro (Daro / Atitinka lūkesčius):** Tai solidus pagrindas, kolega susitvarko.
        - **3 = 🚀 Varo (Varo / Viršija lūkesčius):** Kolega rodo iniciatyvą ir tempia komandą.
        - **4 = ⭐️ Pavyzdys kitiems (Pavyzdys kitiems):** Tai superžvaigždės lygis, kiti turi mokytis iš jo.
        
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
        - **Komentarai:** {safe_comments}
        - **Papildomas kontekstas:** {safe_existing_feedback}
        
        **Generavimo Instrukcija:**
        Parašyk rišlų atsiliepimą lietuvių kalba, kuriame kreipkis į {placeholder}:
        
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

        response_text = OpenRouterService._call_openrouter(
            prompt, user=user, company=company, request_type='feedback_generation'
        )
        return response_text.replace(placeholder, colleague_name) if response_text else response_text

    @staticmethod
    def extract_strengths_weaknesses(feedback_text, comments_text, user=None, company=None):
        """
        Iš tekstinio atsiliepimo išveda stiprybes ir tobulintinas sritis JSON formatu.
        """
        if not feedback_text and not comments_text:
            return {"strengths": [], "improvements": []}

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
            response_text = OpenRouterService._call_openrouter(
                prompt, user=user, company=company, request_type='feedback_analysis'
            )
        except Exception as e:
            print(f"Failed to extract traits: {e}")
            return {"strengths": [], "improvements": []}

        try:
            cleaned_text = response_text.replace('```json', '').replace('```', '').strip()
            data = json.loads(cleaned_text)
            return {
                "strengths": data.get("strengths", []),
                "improvements": data.get("improvements", [])
            }
        except Exception as e:
            print(f"Failed to parse extracted traits: {e}")
            return {"strengths": [], "improvements": []}
