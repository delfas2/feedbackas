import re

translations = {
    # Competencies
    'Komandinis Darbas': 'Teamwork',
    'Komunikacija': 'Communication',
    'Iniciatyvumas': 'Initiative',
    'Techninės Žinios': 'Technical Knowledge',
    'Problemų Sprendimas': 'Problem Solving',
    
    # Results
    'Stiprybės': 'Strengths',
    'Ką tobulinti': 'Areas for Improvement',
    'Kol kas nėra atsiliepimų.': 'No feedback yet.',
    'Kompetencijos Vertinimas': 'Competency Assessment',
    'Nepakanka istorinių duomenų grafikui atvaizduoti.': 'Not enough historical data to display the chart.',
    'Uždaryti': 'Close',
    'Įvyko klaida gaunant duomenis.': 'An error occurred while fetching data.',
    'Įvertinimas': 'Rating',
    'Vertinimas:': 'Rating:',
    
    # My Tasks
    'Mano užduotys': 'My Tasks',
    'Tvarkykite savo atsiliepimų prašymus ir atsakymus.': 'Manage your feedback requests and responses.',
    'Naujausi viršuje': 'Newest first',
    'Pagal terminą': 'By deadline',
    'Užduotys man': 'Tasks for me',
    'Mano išsiųsti prašymai': 'My sent requests',
    'Atsiliepimas apie:': 'Feedback about:',
    'Atsiliepimą inicijavo:': 'Feedback initiated by:',
    'Laukiama atsakymo': 'Awaiting response',
    'Užbaigta': 'Completed',
    'Terminas:': 'Deadline:',
    'Užpildyti': 'Fill out',
    'Peržiūrėti rezultatus': 'View results',
    'Išsiųsta kolegai:': 'Sent to colleague:',
    'Nėra užduočių': 'No tasks',
    'Šiuo metu neturite jokių užduočių.': 'You currently have no tasks.',
    
    # Team member detail (Profile)
    'Skyrius nepriskirtas': 'Department not assigned',
    'Bendras vidurkis': 'Overall average',
    'Atsiliepimų skaičius': 'Number of feedbacks',
    'Užbaigtų apklausų': 'Completed surveys',
    'Raktiniai žodžiai': 'Keywords',
    'Kol kas nėra raktinių žodžių': 'No keywords yet',
    'Kompetencijos': 'Competencies',
    'Savybių įvertinimai': 'Trait ratings',
    'Šis darbuotojas dar neturi unikalių savybių įvertinimų.': 'This employee does not have unique trait ratings yet.',
    'Atsiliepimų istorija': 'Feedback history',
    'Komentaras': 'Comment',
    'Šis darbuotojas dar neturi jokių atsiliepimų istorijos.': 'This employee has no feedback history yet.'
}

with open('locale/en/LC_MESSAGES/django.po', 'r') as f:
    content = f.read()

def replacer(match):
    msgid = match.group(1)
    if msgid in translations:
        return f'msgid "{msgid}"\nmsgstr "{translations[msgid]}"'
    return match.group(0)

content = re.sub(r'msgid "([^"]+)"\nmsgstr ""', replacer, content)

with open('locale/en/LC_MESSAGES/django.po', 'w') as f:
    f.write(content)

print("Translated django.po final")
