import re

translations = {
    'Mano užduotys': 'My Tasks',
    'Visi įvertinimai': 'All Ratings',
    'Visi Įvertinimai - Orbigrow.lt': 'All Ratings - Orbigrow.lt',
    'Vertinamas asmuo': 'Person to Evaluate',
    'Vertintojas': 'Evaluator',
    'Įvertinimas': 'Rating',
    'Priskirti': 'Assign',
    'Pasirinkite padalinį...': 'Select a department...',
    'Užduotys man': 'Assigned to me',
    'Mano išsiųsti prašymai': 'My sent requests'
}

with open('locale/en/LC_MESSAGES/django.po', 'r') as f:
    lines = f.readlines()

new_lines = []
skip_next = False
for i in range(len(lines)):
    if skip_next:
        skip_next = False
        continue
    
    line = lines[i]
    if line.startswith('msgid "'):
        msgid = line[7:-2]
        if msgid in translations:
            new_lines.append(line)
            # Find next msgstr
            for j in range(i+1, len(lines)):
                if lines[j].startswith('msgstr "'):
                    new_lines.append(f'msgstr "{translations[msgid]}"\n')
                    # We need to skip this line when we reach it in the outer loop
                    # But the outer loop is i, so we need to know how many lines to skip
                    # Actually, we can just replace it and use a flag
                    break
            # We found the msgid, now we skip until msgstr is handled
            # Wait, the loop will continue from i+1.
            # I'll use a more robust way.
            pass
    
# Actually, I'll use regex for whole blocks
content = "".join(lines)

for lt, en in translations.items():
    # Replace msgstr for specific msgid
    # Using negative lookahead to avoid matching other msgids
    pattern = r'(msgid "' + re.escape(lt) + r'"\n)(msgstr "[^"]*")'
    content = re.sub(pattern, r'\1msgstr "' + en + r'"', content)

with open('locale/en/LC_MESSAGES/django.po', 'w') as f:
    f.write(content)

print("Fixed PO errors")
