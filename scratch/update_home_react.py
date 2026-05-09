import re

with open('templates/home.html', 'r') as f:
    content = f.read()

# Fix React strings in verbatim block
content = content.replace('title: item.label || `Žingsnis ${i + 1}`', 'title: item.label || `{% endverbatim %}{% trans "Žingsnis" %}{% verbatim %} ${i + 1}`')
content = content.replace('Kraunama...', '{% endverbatim %}{% trans "Kraunama..." %}{% verbatim %}')
content = content.replace('Grįžtamojo ryšio dar nėra.', '{% endverbatim %}{% trans "Grįžtamojo ryšio dar nėra." %}{% verbatim %}')
content = content.replace('Kaip pradėti', '{% endverbatim %}{% trans "Kaip pradėti" %}{% verbatim %}')
content = content.replace('Gauti įvertinimai — {selectedYear}', '{% endverbatim %}{% trans "Gauti įvertinimai" %}{% verbatim %} — {selectedYear}')

with open('templates/home.html', 'w') as f:
    f.write(content)

print("Updated home.html React strings with verbatim handling")
