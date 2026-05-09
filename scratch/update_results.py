import re

with open('templates/results.html', 'r') as f:
    content = f.read()

if '{% load i18n %}' not in content:
    content = content.replace('{% extends "base.html" %}', '{% extends "base.html" %}\n{% load i18n %}')

# Nav/Headers
content = content.replace('Mano rezultatai', '{% trans "Mano rezultatai" %}')
content = content.replace('Jūsų asmeninio tobulėjimo suvestinė.', '{% trans "Jūsų asmeninio tobulėjimo suvestinė." %}')
content = content.replace('Visi</a>', '{% trans "Visi" %}</a>')
content = content.replace('Mėnuo</a>', '{% trans "Mėnuo" %}</a>')
content = content.replace('Ketvirtis</a>', '{% trans "Ketvirtis" %}</a>')
content = content.replace('Metai</a>', '{% trans "Metai" %}</a>')

# Sections
content = content.replace('Kompetencijų vertinimas', '{% trans "Kompetencijų vertinimas" %}')
content = content.replace('Kaip jus apibūdina', '{% trans "Kaip jus apibūdina" %}')
content = content.replace('Kol kas nėra raktinių žodžių.', '{% trans "Kol kas nėra raktinių žodžių." %}')
content = content.replace('Gauti atsiliepimai', '{% trans "Gauti atsiliepimai" %}')
content = content.replace('Komentarai', '{% trans "Komentarai" %}')

with open('templates/results.html', 'w') as f:
    f.write(content)

print("Updated results.html")
