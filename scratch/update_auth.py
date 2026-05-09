import re

def update_file(path, translations):
    with open(path, 'r') as f:
        content = f.read()
    
    if '{% load i18n %}' not in content:
        content = "{% load i18n %}\n" + content
    
    for lt, tag in translations.items():
        content = content.replace(lt, f'{{% trans "{lt}" %}}')
    
    with open(path, 'w') as f:
        f.write(content)

# 1. Update login.html
login_translations = {
    'Prisijungimo Forma': 'Prisijungimo Forma',
    'Grįžti į pradžią': 'Grįžti į pradžią',
    'Prisijungti 👋': 'Prisijungti 👋',
    'El. paštas': 'El. paštas',
    'Slaptažodis': 'Slaptažodis',
    'Prisijungti': 'Prisijungti',
    'arba': 'arba',
    'Prisijungti su Microsoft': 'Prisijungti su Microsoft',
    'Dar neturite paskyros?': 'Dar neturite paskyros?',
    'Registruotis': 'Registruotis'
}
update_file('templates/registration/login.html', login_translations)

# 2. Update register.html
register_translations = {
    'Registracijos Forma': 'Registracijos Forma',
    'Sukurti Paskyrą ✨': 'Sukurti Paskyrą ✨',
    'Klaida!': 'Klaida!',
    'Vardas': 'Vardas',
    'Pavardė': 'Pavardė',
    'Įmonė (Nebūtina)': 'Įmonė (Nebūtina)',
    'Pakartokite slaptažodį': 'Pakartokite slaptažodį',
    'Jau turite paskyrą?': 'Jau turite paskyrą?',
    'Prisijunkite': 'Prisijunkite'
}
# Note: 'Registruotis', 'El. paštas', 'Slaptažodis' are already in login_translations
update_file('templates/registration/register.html', register_translations)

print("Updated login.html and register.html")
