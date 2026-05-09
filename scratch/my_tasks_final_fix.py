import re
import os

with open('templates/my_tasks.html', 'r') as f:
    content = f.read()

# Fix modal strings
content = content.replace('Jūsų žinutė / komentaras', '{% trans "Jūsų žinutė / komentaras" %}')
content = content.replace('Terminas *', '{% trans "Terminas *" %}')
# Be careful with Atšaukti/Išsaugoti as they might be used elsewhere
content = content.replace('>Atšaukti</button>', '>{% trans "Atšaukti" %}</button>')
content = content.replace('Išsaugoti\n', '{% trans "Išsaugoti" %}\n')

# Check if Mano užduotys has any hidden characters
# Actually, I'll just re-write that block to be sure
content = re.sub(r'\{% trans "Mano užduotys" %\}', r'{% trans "Mano užduotys" %}', content)

with open('templates/my_tasks.html', 'w') as f:
    f.write(content)

# Also check base.html for anything missed
with open('templates/base.html', 'r') as f:
    base_content = f.read()
# No obvious untranslated headers left there.

print("Final fix for my_tasks.html")
