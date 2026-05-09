import re
import os

def update_file(path, translations):
    if not os.path.exists(path): return
    with open(path, 'r') as f:
        content = f.read()
    
    if '{% load i18n %}' not in content:
        if '{% extends' in content:
            content = re.sub(r'(\{% extends .*? %\})', r'\1\n{% load i18n %}', content)
        else:
            content = "{% load i18n %}\n" + content
    
    for lt in translations:
        content = content.replace(lt, f'{{% trans "{lt}" %}}')
    
    with open(path, 'w') as f:
        f.write(content)

# 1. includes/view_feedback_modal.html
update_file('templates/includes/view_feedback_modal.html', ['Atsiliepimo Peržiūra'])

# 2. my_tasks.html
update_file('templates/my_tasks.html', ['Redaguoti Užklausą'])

# 3. index.html
update_file('templates/index.html', ['AI Kompetencijų Profilis'])

# 4. registration/login.html and register.html (titles/headers)
# I already did these but maybe some missed
update_file('templates/registration/login.html', ['Prisijungti 👋'])
update_file('templates/registration/register.html', ['Sukurti Paskyrą ✨'])

print("Final cleanup of headers done")
