import re

def add_load_i18n(content, extends_tag="{% extends 'base.html' %}"):
    if '{% load i18n %}' not in content:
        return content.replace(extends_tag, f"{extends_tag}\n{{% load i18n %}}")
    return content

# 1. Update my_tasks.html
with open('templates/my_tasks.html', 'r') as f:
    content = f.read()

content = add_load_i18n(content)
content = content.replace('Mano užduotys', '{% trans "Mano užduotys" %}')
content = content.replace('Tvarkykite savo atsiliepimų prašymus ir atsakymus.', '{% trans "Tvarkykite savo atsiliepimų prašymus ir atsakymus." %}')
content = content.replace('Naujausi viršuje', '{% trans "Naujausi viršuje" %}')
content = content.replace('Pagal terminą', '{% trans "Pagal terminą" %}')
content = content.replace('Užduotys man', '{% trans "Užduotys man" %}')
content = content.replace('Mano išsiųsti prašymai', '{% trans "Mano išsiųsti prašymai" %}')
content = content.replace('Atsiliepimas apie:', '{% trans "Atsiliepimas apie:" %}')
content = content.replace('Atsiliepimą inicijavo:', '{% trans "Atsiliepimą inicijavo:" %}')
content = content.replace('Laukiama atsakymo', '{% trans "Laukiama atsakymo" %}')
content = content.replace('Užbaigta', '{% trans "Užbaigta" %}')
content = content.replace('Terminas:', '{% trans "Terminas:" %}')
content = content.replace('Užpildyti', '{% trans "Užpildyti" %}')
content = content.replace('Peržiūrėti rezultatus', '{% trans "Peržiūrėti rezultatus" %}')
content = content.replace('Išsiųsta kolegai:', '{% trans "Išsiųsta kolegai:" %}')
content = content.replace('Nėra užduočių', '{% trans "Nėra užduočių" %}')
content = content.replace('Šiuo metu neturite jokių užduočių.', '{% trans "Šiuo metu neturite jokių užduočių." %}')

with open('templates/my_tasks.html', 'w') as f:
    f.write(content)

# 2. Update team_member_detail.html
with open('templates/team_member_detail.html', 'r') as f:
    content = f.read()

content = add_load_i18n(content, "{% extends \"base.html\" %}")
content = content.replace('Skyrius nepriskirtas', '{% trans "Skyrius nepriskirtas" %}')
content = content.replace('Bendras vidurkis', '{% trans "Bendras vidurkis" %}')
content = content.replace('Atsiliepimų skaičius', '{% trans "Atsiliepimų skaičius" %}')
content = content.replace('Užbaigtų apklausų', '{% trans "Užbaigtų apklausų" %}')
content = content.replace('Raktiniai žodžiai', '{% trans "Raktiniai žodžiai" %}')
content = content.replace('Kol kas nėra raktinių žodžių', '{% trans "Kol kas nėra raktinių žodžių" %}')
content = content.replace('Kompetencijos', '{% trans "Kompetencijos" %}')
content = content.replace('Savybių įvertinimai', '{% trans "Savybių įvertinimai" %}')
content = content.replace('Šis darbuotojas dar neturi <br/> unikalių savybių įvertinimų.', '{% trans "Šis darbuotojas dar neturi unikalių savybių įvertinimų." %}')
content = content.replace('Atsiliepimų istorija', '{% trans "Atsiliepimų istorija" %}')
content = content.replace('Komentaras', '{% trans "Komentaras" %}')
content = content.replace('Šis darbuotojas dar neturi jokių atsiliepimų istorijos.', '{% trans "Šis darbuotojas dar neturi jokių atsiliepimų istorijos." %}')

with open('templates/team_member_detail.html', 'w') as f:
    f.write(content)

print("Updated my_tasks.html and team_member_detail.html")
