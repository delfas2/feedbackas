import re

with open('templates/superadmin_descriptions.html', 'r') as f:
    content = f.read()

# The form starts at <h2 class="text-2xl font-bold text-primary mb-6 border-b pb-2">Priežiūros režimas
# and ends at <div class="pt-6 border-t flex justify-end">
match = re.search(r'(<h2 class="text-2xl font-bold text-primary mb-6 border-b pb-2">Priežiūros režimas.*?)(<div class="pt-6 border-t flex justify-end">)', content, re.DOTALL)
form_content = match.group(1)
end_part = match.group(2)

en_content = re.sub(r'\{\{\s*form\.([a-zA-Z0-9_]+)\s*\}\}', r'{{ form.\1_en }}', form_content)
# Remove boolean toggle in EN
en_content = re.sub(r'<div class="flex items-center justify-between pb-4 border-b border-red-100/50">.*?</div>', '', en_content, flags=re.DOTALL)

tab_html = f"""
            <!-- KALBOS PASIRINKIMO TABAI -->
            <div class="mb-6 border-b border-gray-200">
                <ul class="flex flex-wrap -mb-px text-sm font-medium text-center" id="langTabs" role="tablist">
                    <li class="mr-2" role="presentation">
                        <button class="inline-block p-4 border-b-2 rounded-t-lg text-primary border-primary active font-bold" id="lt-tab" type="button" role="tab" onclick="switchLangTab('lt')">Lietuvių</button>
                    </li>
                    <li class="mr-2" role="presentation">
                        <button class="inline-block p-4 border-b-2 border-transparent rounded-t-lg hover:text-primary hover:border-gray-300 text-gray-500 font-bold" id="en-tab" type="button" role="tab" onclick="switchLangTab('en')">English</button>
                    </li>
                </ul>
            </div>

            <!-- LIETUVIŲ KALBOS LAUKAI -->
            <div id="lt-content" class="tab-pane block">
{form_content}
            </div>

            <!-- ANGLŲ KALBOS LAUKAI -->
            <div id="en-content" class="tab-pane hidden">
{en_content}
            </div>
"""

new_content = content.replace(form_content, tab_html)

# Add script and TinyMCE for EN content
script_addition = """
    document.addEventListener("DOMContentLoaded", function() {
        tinymce.init({
            selector: '#id_security_content, #id_security_content_en',
            height: 400,
            menubar: false,
            plugins: [
                'advlist', 'autolink', 'lists', 'link', 'charmap', 'preview',
                'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
                'insertdatetime', 'media', 'table', 'code', 'help', 'wordcount'
            ],
            toolbar: 'undo redo | blocks | ' +
            'bold italic forecolor | alignleft aligncenter ' +
            'alignright alignjustify | bullist numlist outdent indent | ' +
            'removeformat | help',
            content_style: 'body { font-family:Inter,Helvetica,Arial,sans-serif; font-size:16px; }'
        });
    });

    function switchLangTab(lang) {
        document.getElementById('lt-tab').className = lang === 'lt' ? 'inline-block p-4 border-b-2 rounded-t-lg text-primary border-primary active font-bold' : 'inline-block p-4 border-b-2 border-transparent rounded-t-lg hover:text-primary hover:border-gray-300 text-gray-500 font-bold';
        document.getElementById('en-tab').className = lang === 'en' ? 'inline-block p-4 border-b-2 rounded-t-lg text-primary border-primary active font-bold' : 'inline-block p-4 border-b-2 border-transparent rounded-t-lg hover:text-primary hover:border-gray-300 text-gray-500 font-bold';
        
        document.getElementById('lt-content').className = lang === 'lt' ? 'tab-pane block' : 'tab-pane hidden';
        document.getElementById('en-content').className = lang === 'en' ? 'tab-pane block' : 'tab-pane hidden';
    }
"""

new_content = re.sub(r'document\.addEventListener.*?\}\);', script_addition, new_content, flags=re.DOTALL)

with open('templates/superadmin_descriptions.html', 'w') as f:
    f.write(new_content)

print("HTML Regenerated successfully.")
