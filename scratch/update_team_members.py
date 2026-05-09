import re

with open('templates/team_members.html', 'r') as f:
    content = f.read()

if '{% load i18n %}' not in content:
    content = content.replace('{% extends \'base.html\' %}', '{% extends \'base.html\' %}\n{% load i18n %}')

# Headers
content = content.replace('Komandos nariai', '{% trans "Komandos nariai" %}')
content = content.replace('Bendraukite ir keiskitės grįžtamuoju ryšiu su kolegomis.', '{% trans "Bendraukite ir keiskitės grįžtamuoju ryšiu su kolegomis." %}')

# Member card
content = content.replace('Kolega</p>', '{% trans "Kolega" %}</p>')
content = content.replace('Skyrius nepriskirtas', '{% trans "Skyrius nepriskirtas" %}')
content = content.replace('Reitingas</span>', '{% trans "Reitingas" %}</span>')
content = content.replace('Laukiama', '{% trans "Laukiama" %}')
content = content.replace('Jau turite neužpildytą užklausą', '{% trans "Jau turite neužpildytą užklausą" %}')
content = content.replace('Vertinti', '{% trans "Vertinti" %}')

# Empty state
content = content.replace('Tuščia komanda', '{% trans "Tuščia komanda" %}')
content = content.replace('Jūsų komandoje dar nėra narių. Pakvieskite kolegas prisijungti prie platformos, kad galėtumėte keistis atsiliepimais.', '{% trans "Jūsų komandoje dar nėra narių. Pakvieskite kolegas prisijungti prie platformos, kad galėtumėte keistis atsiliepimais." %}')

with open('templates/team_members.html', 'w') as f:
    f.write(content)

print("Updated team_members.html")
