import re

with open('templates/team_statistics.html', 'r') as f:
    content = f.read()

if '{% load i18n %}' not in content:
    content = content.replace('{% extends "base.html" %}', '{% extends "base.html" %}\n{% load i18n %}')

# Headers
content = content.replace('Komandos statistika', '{% trans "Komandos statistika" %}')
content = content.replace('Bendra komandos kompetencijų ir aktyvumo apžvalga', '{% trans "Bendra komandos kompetencijų ir aktyvumo apžvalga" %}')

# Summary cards
content = content.replace('Komandos vidurkis', '{% trans "Komandos vidurkis" %}')
content = content.replace('Narių skaičius', '{% trans "Narių skaičius" %}')
content = content.replace('Gauta atsiliepimų', '{% trans "Gauta atsiliepimų" %}')
content = content.replace('iš 4', '{% trans "iš 4" %}')
content = content.replace('nariai', '{% trans "nariai" %}')
content = content.replace('iš viso', '{% trans "iš viso" %}')

# Competencies
content = content.replace('Komandos Kompetencijos', '{% trans "Komandos Kompetencijos" %}')
content = content.replace('Nėra pakankamai duomenų kompetencijoms rodyti.', '{% trans "Nėra pakankamai duomenų kompetencijoms rodyti." %}')

# Table
content = content.replace('Narių Įvertinimai', '{% trans "Narių Įvertinimai" %}')
content = content.replace('Darbuotojas</th>', '{% trans "Darbuotojas" %}</th>')
content = content.replace('Atsiliepimų</th>', '{% trans "Atsiliepimų" %}</th>')
content = content.replace('Vidurkis</th>', '{% trans "Vidurkis" %}</th>')
content = content.replace('Lygis</th>', '{% trans "Lygis" %}</th>')

# Levels
content = content.replace('Pavyzdys', '{% trans "Pavyzdys" %}')
content = content.replace('Varo', '{% trans "Varo" %}')
content = content.replace('Daro', '{% trans "Daro" %}')
content = content.replace('Mokosi', '{% trans "Mokosi" %}')

# Empty
content = content.replace('Komandoje kol kas nėra narių su atsiliepimais.', '{% trans "Komandoje kol kas nėra narių su atsiliepimais." %}')

with open('templates/team_statistics.html', 'w') as f:
    f.write(content)

print("Updated team_statistics.html")
