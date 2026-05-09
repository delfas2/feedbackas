import re

translations = {
    'Atsiliepimo Peržiūra': 'Feedback Preview',
    'Redaguoti Užklausą': 'Edit Request',
    'AI Kompetencijų Profilis': 'AI Competency Profile'
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

print("Translated final final")
