import re

with open('locale/en/LC_MESSAGES/django.po', 'r') as f:
    content = f.read()

# Remove all fuzzy lines
content = re.sub(r'#, fuzzy\n', '', content)

# Fix specific translations
translations = {
    'Tęsti pildymą': 'Continue filling',
    'Pildyti atsiliepimą': 'Fill feedback',
    'Atlikta': 'Done',
    'Ar tikrai norite ištrinti šią užduotį?': 'Are you sure you want to delete this task?',
    'Ištrinti': 'Delete',
    'Jokių užduočių': 'No tasks',
    'Šiuo metu neturite jums priskirtų atsiliepimų prašymų.': 'You currently have no feedback requests assigned to you.',
    'Atsiliepimas iš:': 'Feedback from:',
    'Gautas atsakymas': 'Response received',
    'Peržiūrėti': 'View',
    'Redaguoti': 'Edit',
    'Ar tikrai norite ištrinti šį prašymą?': 'Are you sure you want to delete this request?',
    'Tuščia': 'Empty',
    'Jūs dar nesate išsiuntę jokių prašymų.': 'You have not sent any requests yet.'
}

for lt, en in translations.items():
    # Replace msgstr for specific msgid
    # We use regex to find the msgid and replace the following msgstr
    pattern = r'(msgid "' + re.escape(lt) + r'"\n)(msgstr "[^"]*")'
    content = re.sub(pattern, r'\1msgstr "' + en + r'"', content)

with open('locale/en/LC_MESSAGES/django.po', 'w') as f:
    f.write(content)

print("Updated PO with new translations")
