import google.generativeai as genai
from django.conf import settings

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
