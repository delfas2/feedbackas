import re

translations = {
    # Titles
    'Orbigrow.lt': 'Orbigrow.lt',
    'Rezultatai - Orbigrow.lt': 'Results - Orbigrow.lt',
    'Komandos Statistika - Orbigrow.lt': 'Team Statistics - Orbigrow.lt',
    'Mano Užduotys - Orbigrow.lt': 'My Tasks - Orbigrow.lt',
    'Visi Įvertinimai - Orbigrow.lt': 'All Ratings - Orbigrow.lt',
    'Įmonės Valdymas - Orbigrow.lt': 'Company Management - Orbigrow.lt',
    'Nario Profilis - Orbigrow.lt': 'Member Profile - Orbigrow.lt',
    'Individuali forma': 'Individual Form',
    'Klausimyno Statistika - Orbigrow.lt': 'Questionnaire Statistics - Orbigrow.lt',
    'Kolegos Apklausa - Orbigrow.lt': 'Colleague Survey - Orbigrow.lt',
    
    # questionnaires/list.html
    'Kurkite ir valdykite unikalius atsiliepimų klausimynus.': 'Create and manage unique feedback questionnaires.',
    'Komandinė forma': 'Team Form',
    'Kurti klausimyną': 'Create Questionnaire',
    'Komandinė': 'Team',
    'Asmeninė': 'Personal',
    'Nėra savybių': 'No traits',
    'Statistika': 'Statistics',
    'Redaguoti': 'Edit',
    'Siųsti': 'Send',
    'Ištrinti': 'Delete',
    'Kol kas neturite klausimynų': 'You don\'t have any questionnaires yet',
    'Kurti pirmąjį klausimyną': 'Create your first questionnaire',
    'Naujas klausimynas': 'New Questionnaire',
    'Klausimyno pavadinimas': 'Questionnaire Title',
    'Savybių debesis': 'Trait Cloud',
    'paspauskite norimas savybes': 'click the desired traits',
    'Pridėti savo savybę': 'Add your own trait',
    'Įveskite savybės pavadinimą...': 'Enter trait name...',
    'Pridėti': 'Add',
    'Pasirinktos savybės': 'Selected Traits',
    'Dar nepasirinkta jokia savybė': 'No traits selected yet',
    'Atšaukti': 'Cancel',
    'Sukurti': 'Create',
    'Nauja komandinė forma': 'New Team Form',
    'Pasirinkite komandą': 'Select Team',
    '-- Pasirinkite komandą --': '-- Select Team --',
    'Sukurti komandinę': 'Create Team Form',
    'Redaguoti klausimyną': 'Edit Questionnaire',
    'Išsaugoti': 'Save',
    'Siųsti klausimyną': 'Send Questionnaire',
    'Pasirinkite kolegą (-as), kurių prašysite užpildyti šį klausimyną.': 'Select colleague(s) you want to ask to fill out this questionnaire.',
    'Pasirinktas klausimynas': 'Selected Questionnaire',
    'Kam norite jį išsiųsti?': 'Who do you want to send it to?',
    'Ieškoti kolegų...': 'Search colleagues...',
    'Nėra kolegų, kuriems galėtumėte išsiųsti': 'No colleagues to send to',
    'Turite pasirinkti bent vieną kolegą.': 'You must select at least one colleague.',
    'Ar tikrai norite ištrinti?': 'Are you sure you want to delete this?',
    'Kurkite asmeninius ar komandinius klausimynus ir siųskite juos kolegoms, kad gautumėte struktūruotą grįžtamąjį ryšį.': 'Create personal or team questionnaires and send them to colleagues to get structured feedback.',
    
    # questionnaires/statistics.html
    'Statistika:': 'Statistics:',
    'Bendras Įvertinimas': 'Overall Rating',
    'Visų atsakymų vidurkis': 'Average of all responses',
    'Gauta Atsakymų': 'Answers Received',
    'Rezultatų Dinamika': 'Results Dynamics',
    'Kompetencijų Vidurkiai': 'Competency Averages',
    'Kolegų Paminėti Raktiniai Žodžiai': 'Keywords Mentioned by Colleagues',
    'Kol kas nėra raktinių žodžių.': 'No keywords yet.',
    'Laisvos formos komentarai': 'Open-form comments',
    'Trūksta duomenų grafiko atvaizdavimui.': 'Missing data for chart display.',
    
    # fill_feedback.html
    'Mokosi': 'Learning',
    'Daro': 'Doing',
    'Varo': 'Driving',
    'Pavyzdys': 'Role Model',
    'Pasirinkite vieną iš lygių aukščiau': 'Choose one of the levels above',
    'Įveskite žodį ir spauskite Enter arba kablelį...': 'Enter a word and press Enter or comma...',
    'Rinktis iš debesies': 'Choose from cloud',
    'Raktinių žodžių debesis': 'Keyword Cloud',
    
    # home.html
    'Komandos veikla': 'Team Activity',
    'Visi įvykiai': 'All Events',
    'Grįžtamasis ryšys': 'Feedback',
    'Žingsnis': 'Step',
    'Kraunama...': 'Loading...',
    'Grįžtamojo ryšio dar nėra.': 'No feedback yet.',
    'Kaip pradėti': 'How to start',
    'Gauti įvertinimai': 'Ratings received',
    
    # index.html
    'Susisiekite su mumis': 'Contact us',
    'Vardas ir Pavardė': 'Full Name',
    'Telefono numeris': 'Phone Number',
    'Darbuotojų skaičius jūsų įmonėje': 'Number of employees in your company',
    'Pasirinkite...': 'Select...',
    'Jūsų Žinutė': 'Your Message',
    'Trumpai apibūdinkite savo poreikius...': 'Briefly describe your needs...',
    'Siųsti užklausą': 'Send request'
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

print("Translated django.po batch")
