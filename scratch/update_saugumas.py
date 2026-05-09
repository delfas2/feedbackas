import re

with open('templates/saugumas.html', 'r') as f:
    content = f.read()

# Add loads
if '{% load i18n translation_tags %}' not in content:
    content = content.replace('{% load static %}', '{% load static i18n translation_tags %}')

# Update dynamic fields
def repl_dynamic(match):
    field = match.group(1)
    return f"{{{{ page_description|translate_field:'{field}' }}}}"

content = re.sub(r'\{\{\s*page_description\.([a-zA-Z0-9_]+)\s*\}\}', repl_dynamic, content)

# Update static strings
content = content.replace('Pradžia</a>', '{% trans "Pradžia" %}</a>')
content = content.replace('Apie mus</a>', '{% trans "Apie mus" %}</a>')
content = content.replace('Prietaisų skydelis', '{% trans "Prietaisų skydelis" %}')
content = content.replace('Prisijungti</a>', '{% trans "Prisijungti" %}</a>')
content = content.replace('Saugumo Užtikrinimas', '{% trans "Saugumo Užtikrinimas" %}')
content = content.replace('Jūsų duomenų saugumas ir privatumas yra mūsų prioritetas.', '{% trans "Jūsų duomenų saugumas ir privatumas yra mūsų prioritetas." %}')

# Update title
content = content.replace('<title>Saugumo užtikrinimas - Orbigrow.lt</title>', '<title>{% trans "Saugumo užtikrinimas" %} - Orbigrow.lt</title>')

with open('templates/saugumas.html', 'w') as f:
    f.write(content)

print("Updated saugumas.html")
