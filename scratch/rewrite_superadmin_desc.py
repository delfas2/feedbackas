import re

with open('templates/superadmin_descriptions.html', 'r') as f:
    content = f.read()

match = re.search(r'(<h2 class="text-2xl font-bold text-primary mb-6 border-b pb-2">Priežiūros režimas.*?)(<div class="mt-8">)', content, re.DOTALL)
if not match:
    print("Could not match form content")
    exit(1)

form_content = match.group(1)
button_content = match.group(2)

en_content = re.sub(r'\{\{\s*form\.([a-zA-Z0-9_]+)\s*\}\}', r'{{ form.\1_en }}', form_content)

# We want to remove the boolean switch from the EN tab to avoid confusion.
# The boolean switch is:
#                 <div class="flex items-center justify-between pb-4 border-b border-red-100/50">
#                     <div>
#                         <h3 class="text-lg font-bold text-red-800">Išjungti pradinį puslapį</h3>
#                         <p class="text-sm text-red-600">Įjungus šį jungiklį, lankytojams vietoje pradinio puslapio bus rodomas pranešimas.</p>
#                     </div>
#                     <label class="relative inline-flex items-center cursor-pointer">
#                         {{ form.maintenance_mode_en }}
#                     </label>
#                 </div>

en_content = re.sub(r'<div class="flex items-center justify-between pb-4 border-b border-red-100/50">.*?</div>', '', en_content, flags=re.DOTALL)

tabbed_content = f"""
            <!-- TABS -->
            <div class="mb-6 border-b border-gray-200">
                <ul class="flex flex-wrap -mb-px text-sm font-medium text-center" id="langTabs" role="tablist">
                    <li class="mr-2" role="presentation">
                        <button class="inline-block p-4 border-b-2 rounded-t-lg text-primary border-primary active" id="lt-tab" type="button" role="tab" onclick="switchLangTab('lt')">Lietuvių</button>
                    </li>
                    <li class="mr-2" role="presentation">
                        <button class="inline-block p-4 border-b-2 border-transparent rounded-t-lg hover:text-primary hover:border-gray-300 text-gray-500" id="en-tab" type="button" role="tab" onclick="switchLangTab('en')">English</button>
                    </li>
                </ul>
            </div>

            <!-- LT CONTENT -->
            <div id="lt-content" class="tab-pane block">
{form_content}
            </div>

            <!-- EN CONTENT -->
            <div id="en-content" class="tab-pane hidden">
{en_content}
            </div>
"""

new_content = content.replace(form_content, tabbed_content)

# Add script
script = """
{% endblock %}

{% block extra_js %}
<script>
    function switchLangTab(lang) {
        // Update tabs
        document.getElementById('lt-tab').className = lang === 'lt' ? 'inline-block p-4 border-b-2 rounded-t-lg text-primary border-primary active' : 'inline-block p-4 border-b-2 border-transparent rounded-t-lg hover:text-primary hover:border-gray-300 text-gray-500';
        document.getElementById('en-tab').className = lang === 'en' ? 'inline-block p-4 border-b-2 rounded-t-lg text-primary border-primary active' : 'inline-block p-4 border-b-2 border-transparent rounded-t-lg hover:text-primary hover:border-gray-300 text-gray-500';
        
        // Update content
        document.getElementById('lt-content').className = lang === 'lt' ? 'tab-pane block' : 'tab-pane hidden';
        document.getElementById('en-content').className = lang === 'en' ? 'tab-pane block' : 'tab-pane hidden';
    }
</script>
{% endblock %}
"""

new_content = new_content.replace('{% endblock %}', script)

with open('templates/superadmin_descriptions.html', 'w') as f:
    f.write(new_content)

print("Done")
