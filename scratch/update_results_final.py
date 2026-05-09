import re

with open('templates/results.html', 'r') as f:
    content = f.read()

# Already has load i18n from previous step

content = content.replace('Stiprybės', '{% trans "Stiprybės" %}')
content = content.replace('Ką tobulinti', '{% trans "Ką tobulinti" %}')
content = content.replace('Kol kas nėra atsiliepimų.', '{% trans "Kol kas nėra atsiliepimų." %}')
content = content.replace('Kompeticijos Vertinimas', '{% trans "Kompetencijos Vertinimas" %}') # Fixed typo in replacement too
content = content.replace('Nepakanka istorinių duomenų grafikui atvaizduoti.', '{% trans "Nepakanka istorinių duomenų grafikui atvaizduoti." %}')
content = content.replace('Uždaryti', '{% trans "Uždaryti" %}')
content = content.replace('Įvyko klaida gaunant duomenis.', '{% trans "Įvyko klaida gaunant duomenis." %}')

# In JS part
content = content.replace("'Įvertinimas'", " '{% trans 'Įvertinimas' %}' ")
content = content.replace("' Vertinimas: '", " '{% trans 'Vertinimas:' %} ' ")

with open('templates/results.html', 'w') as f:
    f.write(content)

print("Updated results.html final")
