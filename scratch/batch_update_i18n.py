import re
import os

def update_file(path, translations, add_i18n=True):
    if not os.path.exists(path): return
    with open(path, 'r') as f:
        content = f.read()
    
    if add_i18n and '{% load i18n %}' not in content:
        # Try to add after extends or at top
        if '{% extends' in content:
            content = re.sub(r'(\{% extends .*? %\})', r'\1\n{% load i18n %}', content)
        else:
            content = "{% load i18n %}\n" + content
    
    # Sort translations by length descending to avoid partial matches
    sorted_keys = sorted(translations.keys(), key=len, reverse=True)
    
    for lt in sorted_keys:
        # Avoid double wrapping
        if f'{{% trans "{lt}" %}}' in content: continue
        # Simple replacement for exact matches in text nodes
        content = content.replace(lt, f'{{% trans "{lt}" %}}')
    
    with open(path, 'w') as f:
        f.write(content)

# 1. questionnaires/list.html
q_list_trans = {
    'Individuali forma': 'Individuali forma',
    'Kurkite ir valdykite unikalius atsiliepimų klausimynus.': 'Kurkite ir valdykite unikalius atsiliepimų klausimynus.',
    'Komandinė forma': 'Komandinė forma',
    'Kurti klausimyną': 'Kurti klausimyną',
    'Komandinė': 'Komandinė',
    'Asmeninė': 'Asmeninė',
    'Nėra savybių': 'Nėra savybių',
    'Statistika': 'Statistika',
    'Redaguoti': 'Redaguoti',
    'Siųsti': 'Siųsti',
    'Ištrinti': 'Ištrinti',
    'Kol kas neturite klausimynų': 'Kol kas neturite klausimynų',
    'Kurti pirmąjį klausimyną': 'Kurti pirmąjį klausimyną',
    'Naujas klausimynas': 'Naujas klausimynas',
    'Klausimyno pavadinimas': 'Klausimyno pavadinimas',
    'Savybių debesis': 'Savybių debesis',
    'paspauskite norimas savybes': 'paspauskite norimas savybes',
    'Pridėti savo savybę': 'Pridėti savo savybę',
    'Įveskite savybės pavadinimą...': 'Įveskite savybės pavadinimą...',
    'Pridėti': 'Pridėti',
    'Pasirinktos savybės': 'Pasirinktos savybės',
    'Dar nepasirinkta jokia savybė': 'Dar nepasirinkta jokia savybė',
    'Atšaukti': 'Atšaukti',
    'Sukurti': 'Sukurti',
    'Nauja komandinė forma': 'Nauja komandinė forma',
    'Pasirinkite komandą': 'Pasirinkite komandą',
    '-- Pasirinkite komandą --': '-- Pasirinkite komandą --',
    'Sukurti komandinę': 'Sukurti komandinę',
    'Redaguoti klausimyną': 'Redaguoti klausimyną',
    'Išsaugoti': 'Išsaugoti',
    'Siųsti klausimyną': 'Siųsti klausimyną',
    'Pasirinkite kolegą (-as), kurių prašysite užpildyti šį klausimyną.': 'Pasirinkite kolegą (-as), kurių prašysite užpildyti šį klausimyną.',
    'Pasirinktas klausimynas': 'Pasirinktas klausimynas',
    'Kam norite jį išsiųsti?': 'Kam norite jį išsiųsti?',
    'Ieškoti kolegų...': 'Ieškoti kolegų...',
    'Nėra kolegų, kuriems galėtumėte išsiųsti': 'Nėra kolegų, kuriems galėtumėte išsiųsti',
    'Turite pasirinkti bent vieną kolegą.': 'Turite pasirinkti bent vieną kolegą.',
    'Ar tikrai norite ištrinti?': 'Ar tikrai norite ištrinti?',
    'Kurkite asmeninius ar komandinius klausimynus ir siųskite juos kolegoms, kad gautumėte struktūruotą grįžtamąjį ryšį.': 'Kurkite asmeninius ar komandinius klausimynus ir siųskite juos kolegoms, kad gautumėte struktūruotą grįžtamąjį ryšį.'
}
update_file('templates/questionnaires/list.html', q_list_trans)

# 2. questionnaires/statistics.html
q_stats_trans = {
    'Statistika:': 'Statistika:',
    'Bendras Įvertinimas': 'Bendras Įvertinimas',
    'Visų atsakymų vidurkis': 'Visų atsakymų vidurkis',
    'Gauta Atsakymų': 'Gauta Atsakymų',
    'Rezultatų Dinamika': 'Rezultatų Dinamika',
    'Kompetencijų Vidurkiai': 'Kompetencijų Vidurkiai',
    'Kolegų Paminėti Raktiniai Žodžiai': 'Kolegų Paminėti Raktiniai Žodžiai',
    'Kol kas nėra raktinių žodžių.': 'Kol kas nėra raktinių žodžių.',
    'Laisvos formos komentarai': 'Laisvos formos komentarai',
    'Kol kas nėra atsiliepimų.': 'Kol kas nėra atsiliepimų.',
    'Trūksta duomenų grafiko atvaizdavimui.': 'Trūksta duomenų grafiko atvaizdavimui.'
}
update_file('templates/questionnaires/statistics.html', q_stats_trans)

# 3. fill_feedback.html (some strings missed in previous rounds)
fill_trans = {
    'Mokosi': 'Mokosi',
    'Daro': 'Daro',
    'Varo': 'Varo',
    'Pavyzdys': 'Pavyzdys',
    'Pasirinkite vieną iš lygių aukščiau': 'Pasirinkite vieną iš lygių aukščiau',
    'Raktiniai žodžiai': 'Raktiniai žodžiai',
    'Įveskite žodį ir spauskite Enter arba kablelį...': 'Įveskite žodį ir spauskite Enter arba kablelį...',
    'Rinktis iš debesies': 'Rinktis iš debesies',
    'Raktinių žodžių debesis': 'Raktinių žodžių debesis'
}
update_file('templates/fill_feedback.html', fill_trans)

# 4. home.html (remaining ones)
home_trans = {
    'Komandos veikla': 'Komandos veikla',
    'Visi įvykiai': 'Visi įvykiai',
    'Grįžtamasis ryšys': 'Grįžtamasis ryšys'
}
update_file('templates/home.html', home_trans)

# 5. index.html (Contact modal and footer)
index_trans = {
    'Susisiekite su mumis': 'Susisiekite su mumis',
    'Vardas ir Pavardė': 'Vardas ir Pavardė',
    'El. paštas': 'El. paštas',
    'Telefono numeris': 'Telefono numeris',
    'Darbuotojų skaičius jūsų įmonėje': 'Darbuotojų skaičius jūsų įmonėje',
    'Pasirinkite...': 'Pasirinkite...',
    'Jūsų Žinutė': 'Jūsų Žinutė',
    'Trumpai apibūdinkite savo poreikius...': 'Trumpai apibūdinkite savo poreikius...',
    'Siųsti užklausą': 'Siųsti užklausą'
}
update_file('templates/index.html', index_trans, add_i18n=False) # already loaded

print("Batch updated templates for i18n")
