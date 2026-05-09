import re

translations = {
    # Auth
    'Prisijungimo Forma': 'Login Form',
    'Grįžti į pradžią': 'Return to Home',
    'Prisijungti 👋': 'Login 👋',
    'El. paštas': 'Email',
    'Slaptažodis': 'Password',
    'Prisijungti': 'Login',
    'arba': 'or',
    'Prisijungti su Microsoft': 'Sign in with Microsoft',
    'Dar neturite paskyros?': 'Don\'t have an account yet?',
    'Registruotis': 'Register',
    'Registracijos Forma': 'Registration Form',
    'Sukurti Paskyrą ✨': 'Create Account ✨',
    'Klaida!': 'Error!',
    'Vardas': 'First Name',
    'Pavardė': 'Last Name',
    'Įmonė (Nebūtina)': 'Company (Optional)',
    'Pakartokite slaptažodį': 'Repeat password',
    'Jau turite paskyrą?': 'Already have an account?',
    'Prisijunkite': 'Sign in',
    
    # Company structure
    'struktūra': 'structure',
    'Valdykite komandas ir priskirkite darbuotojus.': 'Manage teams and assign employees.',
    'Padalinys': 'Department',
    'Organizacinis Medis': 'Organizational Tree',
    'Struktūra dar nesukurta.': 'Structure not created yet.',
    'Nepriskirti Darbuotojai': 'Unassigned Employees',
    'Pasirinkite padalinį...': 'Select a department...',
    'Priskirti': 'Assign',
    'Visi darbuotojai priskirti.': 'All employees are assigned.',
    'Naujas Padalinys': 'New Department',
    'Įveskite padalinio informaciją': 'Enter department information',
    'Pavadinimas': 'Name',
    'Tėvinis padalinys': 'Parent Department',
    'Vadovas': 'Manager',
    'Atšaukti': 'Cancel',
    'Sukurti': 'Create'
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

print("Translated django.po final v2")
