import re

with open('templates/fill_feedback.html', 'r') as f:
    content = f.read()

if '{% load i18n %}' not in content:
    content = content.replace('{% extends \'base.html\' %}', '{% extends \'base.html\' %}\n{% load i18n %}')

# Headers
content = content.replace('Atgal', '{% trans "Atgal" %}')
content = content.replace('Atsiliepimas apie', '{% trans "Atsiliepimas apie" %}')

# Battery segments
content = content.replace('Mokosi</span>', '{% trans "Mokosi" %}</span>')
content = content.replace('Daro</span>', '{% trans "Daro" %}</span>')
content = content.replace('Varo</span>', '{% trans "Varo" %}</span>')
content = content.replace('Pavyzdys</span>', '{% trans "Pavyzdys" %}</span>')
content = content.replace('Pasirinkite vieną iš lygių aukščiau', '{% trans "Pasirinkite vieną iš lygių aukščiau" %}')

# Sections
content = content.replace('Raktiniai žodžiai', '{% trans "Raktiniai žodžiai" %}')
content = content.replace('Įveskite žodį ir spauskite Enter arba kablelį...', '{% trans "Įveskite žodį ir spauskite Enter arba kablelį..." %}')
content = content.replace('Rinktis iš debesies', '{% trans "Rinktis iš debesies" %}')
content = content.replace('Raktinių žodžių debesis', '{% trans "Raktinių žodžių debesis" %}')
content = content.replace('Komentarai', '{% trans "Komentarai" %}')
content = content.replace('Įrašykite laisvos formos komentarus apie kolegą...', '{% trans "Įrašykite laisvos formos komentarus apie kolegą..." %}')
content = content.replace('Išsamus atsiliepimas (AI)', '{% trans "Išsamus atsiliepimas (AI)" %}')
content = content.replace('Pateikite išsamesnį komentarą...', '{% trans "Pateikite išsamesnį komentarą..." %}')

# Buttons
content = content.replace('Generuoti AI juodraštį', '{% trans "Generuoti AI juodraštį" %}')
content = content.replace('Pasirinkite visas savybes ir bent 3 raktinius žodžius', '{% trans "Pasirinkite visas savybes ir bent 3 raktinius žodžius" %}')
content = content.replace('Patvirtinti ir siųsti', '{% trans "Patvirtinti ir siųsti" %}')

with open('templates/fill_feedback.html', 'w') as f:
    f.write(content)

print("Updated fill_feedback.html")
