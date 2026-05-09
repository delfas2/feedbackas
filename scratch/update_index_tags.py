import re

with open('templates/index.html', 'r') as f:
    content = f.read()

# Make sure we load the new tags at the top
if '{% load translation_tags %}' not in content:
    content = content.replace('{% load static i18n %}', '{% load static i18n translation_tags %}')

# Find all instances of {{ page_description.some_field }} and replace them
def repl(match):
    field = match.group(1)
    if field == 'maintenance_mode':
        return match.group(0) # don't touch boolean
    return f"{{{{ page_description|translate_field:'{field}' }}}}"

new_content = re.sub(r'\{\{\s*page_description\.([a-zA-Z0-9_]+)\s*\}\}', repl, content)

with open('templates/index.html', 'w') as f:
    f.write(new_content)

print("Updated index.html tags.")
