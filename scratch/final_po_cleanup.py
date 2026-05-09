import re

with open('locale/en/LC_MESSAGES/django.po', 'r') as f:
    content = f.read()

# Remove all fuzzy lines
content = re.sub(r'#, fuzzy\n', '', content)

# Fix specific wrong translations
translations = {
    'Mano užduotys': 'My Tasks',
    'Visi įvertinimai': 'All Ratings',
    'Jūsų žinutė / komentaras': 'Your message / comment',
    'Terminas *': 'Deadline *',
    'Redaguoti Užklausą': 'Edit Request',
    'Išsaugoti': 'Save',
    'Atšaukti': 'Cancel'
}

for lt, en in translations.items():
    pattern = r'(msgid "' + re.escape(lt) + r'"\n)(msgstr "[^"]*")'
    content = re.sub(pattern, r'\1msgstr "' + en + r'"', content)

with open('locale/en/LC_MESSAGES/django.po', 'w') as f:
    f.write(content)
