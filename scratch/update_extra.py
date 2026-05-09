import re

# 1. Update company_management.html
with open('templates/company_management.html', 'r') as f:
    content = f.read()

if '{% load i18n %}' not in content:
    content = content.replace("{% extends 'base.html' %}", "{% extends 'base.html' %}\n{% load i18n %}")

content = content.replace('struktūra', '{% trans "struktūra" %}')
content = content.replace('Valdykite komandas ir priskirkite darbuotojus.', '{% trans "Valdykite komandas ir priskirkite darbuotojus." %}')
content = content.replace('Padalinys', '{% trans "Padalinys" %}')
content = content.replace('Organizacinis Medis', '{% trans "Organizacinis Medis" %}')
content = content.replace('Struktūra dar nesukurta.', '{% trans "Struktūra dar nesukurta." %}')
content = content.replace('Nepriskirti Darbuotojai', '{% trans "Nepriskirti Darbuotojai" %}')
content = content.replace('Pasirinkite padalinį...', '{% trans "Pasirinkite padalinį..." %}')
content = content.replace('Priskirti', '{% trans "Priskirti" %}')
content = content.replace('Visi darbuotojai priskirti.', '{% trans "Visi darbuotojai priskirti." %}')
content = content.replace('Naujas Padalinys', '{% trans "Naujas Padalinys" %}')
content = content.replace('Įveskite padalinio informaciją', '{% trans "Įveskite padalinio informaciją" %}')
content = content.replace('Pavadinimas', '{% trans "Pavadinimas" %}')
content = content.replace('Tėvinis padalinys', '{% trans "Tėvinis padalinys" %}')
content = content.replace('Vadovas', '{% trans "Vadovas" %}')
content = content.replace('Atšaukti', '{% trans "Atšaukti" %}')
content = content.replace('Sukurti', '{% trans "Sukurti" %}')

with open('templates/company_management.html', 'w') as f:
    f.write(content)

print("Updated company_management.html")
