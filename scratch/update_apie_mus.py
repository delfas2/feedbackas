import re

with open('templates/apie_mus.html', 'r') as f:
    content = f.read()

# Add loads
if '{% load i18n translation_tags %}' not in content:
    content = content.replace('{% load static %}', '{% load static i18n translation_tags %}')

# Update dynamic fields
def repl_dynamic(match):
    field = match.group(1)
    return f"{{{{ page_description|translate_field:'{field}' }}}}"

content = re.sub(r'\{\{\s*page_description\.([a-zA-Z0-9_]+)\s*\}\}', repl_dynamic, content)

# Update static strings in Nav
content = content.replace('Pradžia</a>', '{% trans "Pradžia" %}</a>')
content = content.replace('Apie\n                    mus</a>', '{% trans "Apie mus" %}</a>')
content = content.replace('Saugumas</a>', '{% trans "Saugumas" %}</a>')
content = content.replace('Prietaisų skydelis', '{% trans "Prietaisų skydelis" %}')
content = content.replace('Prisijungti</a>', '{% trans "Prisijungti" %}</a>')

# Update page title
content = content.replace('<title>Apie mus - Orbigrow.lt</title>', '<title>{% trans "Apie mus" %} - Orbigrow.lt</title>')

with open('templates/apie_mus.html', 'w') as f:
    f.write(content)

print("Updated apie_mus.html")
