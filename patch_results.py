import sys

def patch_results_html():
    with open('/tmp/results_head.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace the competency div
    target_div = """                    {% for comp in competencies %}
                    <div>
                        <div class="flex justify-between mb-1">
                            <span class="text-sm font-medium text-gray-700">{{ comp.name }}</span>
                            <span class="text-sm font-bold text-purple-600">{{ comp.score|floatformat }}/4</span>
                        </div>
                        <div class="w-full bg-gray-100 rounded-full h-3">
                            <div class="bg-purple-500 h-3 rounded-full"
                                style="width: {% widthratio comp.score 4 100 %}%"></div>
                        </div>
                    </div>"""
    
    replacement_div = """                    {% for comp in competencies %}
                    <div class="cursor-pointer hover:bg-gray-50 transition-colors p-2 -mx-2 rounded-lg group" onclick="openCompetencyModal('{{ comp.name }}')">
                        <div class="flex justify-between mb-1 items-center">
                            <span class="text-sm font-medium text-gray-700 group-hover:text-purple-700 flex items-center gap-1">
                                {{ comp.name }}
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-3 h-3 text-gray-400 group-hover:text-purple-500 opacity-0 group-hover:opacity-100 transition-opacity">
                                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
                                </svg>
                            </span>
                            <span class="text-sm font-bold text-purple-600 group-hover:text-purple-800">{{ comp.score|floatformat }}/4</span>
                        </div>
                        <div class="w-full bg-gray-100 rounded-full h-3">
                            <div class="bg-purple-500 h-3 rounded-full group-hover:bg-purple-600 transition-colors"
                                style="width: {% widthratio comp.score 4 100 %}%"></div>
                        </div>
                    </div>"""

    if target_div not in content:
        print("COULD NOT FIND TARGET DIV")
        return
        
    content = content.replace(target_div, replacement_div)

    # 2. Append the modal
    modal_and_scripts = """
    <!-- Competency Trend Modal -->
    <div id="competencyModal" class="fixed inset-0 overflow-y-auto h-full w-full hidden transition-opacity"
        style="background-color: rgba(75, 85, 99, 0.5); z-index: 50;">
        <div class="relative top-20 mx-auto w-11/12 sm:max-w-2xl border shadow-xl rounded-xl bg-white overflow-hidden">
            <div class="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-bold text-gray-900 flex items-center gap-2">
                        <svg class="w-6 h-6 text-purple-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18 9 11.25l4.306 4.306a11.95 11.95 0 0 1 5.814-5.518l2.74-1.22m0 0-5.94-2.281m5.94 2.28-2.28 5.941" />
                        </svg>
                        <span id="competencyModalTitle">Kompeticijos Vertinimas</span>
                    </h3>
                    <button type="button" onclick="closeCompetencyModal()" class="text-gray-400 hover:text-gray-500 focus:outline-none">
                        <span class="sr-only">Uždaryti</span>
                        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
                
                <div class="relative h-64 w-full">
                    <canvas id="competencyChart"></canvas>
                </div>
                <p id="competencyModalEmptyState" class="hidden text-center text-gray-500 mt-10">Nepakanka istorinių duomenų grafikui atvaizduoti.</p>
            </div>
            <div class="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                <button type="button" onclick="closeCompetencyModal()"
                    class="mt-3 inline-flex w-full justify-center rounded-lg bg-white px-5 py-2 text-sm font-medium text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto">
                    Uždaryti
                </button>
            </div>
        </div>
    </div>

</main>
{% endblock %}

{% block scripts %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
    let compChartInstance = null;

    function openCompetencyModal(competencyName) {
        document.getElementById('competencyModal').classList.remove('hidden');
        document.getElementById('competencyModalTitle').textContent = competencyName + ' - Vertinimo Istorija';
        document.getElementById('competencyModalEmptyState').classList.add('hidden');
        
        const ctx = document.getElementById('competencyChart').getContext('2d');
        if (compChartInstance) {
            compChartInstance.destroy();
        }

        fetch(`/api/competency_trend/${encodeURIComponent(competencyName)}/`)
            .then(res => res.json())
            .then(data => {
                if (!data.trend || data.trend.length === 0) {
                    document.getElementById('competencyChart').classList.add('hidden');
                    document.getElementById('competencyModalEmptyState').classList.remove('hidden');
                    return;
                }

                document.getElementById('competencyChart').classList.remove('hidden');

                const labels = data.trend.map(item => item.date);
                const scores = data.trend.map(item => item.score);
                const projects = data.trend.map(item => item.project);

                compChartInstance = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Įvertinimas',
                            data: scores,
                            borderColor: '#8B5CF6',
                            backgroundColor: 'rgba(139, 92, 246, 0.1)',
                            borderWidth: 3,
                            pointBackgroundColor: '#A855F7',
                            pointBorderColor: '#fff',
                            pointHoverBackgroundColor: '#fff',
                            pointHoverBorderColor: '#A855F7',
                            pointRadius: 5,
                            pointHoverRadius: 7,
                            fill: true,
                            tension: 0.3
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                min: 0,
                                max: 4,
                                ticks: { stepSize: 1 }
                            }
                        },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    title: function(context) {
                                        return projects[context[0].dataIndex] + ' (' + context[0].label + ')';
                                    },
                                    label: function(context) {
                                        return ' Vertinimas: ' + context.raw + ' / 4';
                                    }
                                }
                            }
                        }
                    }
                });
            })
            .catch(err => {
                console.error("Error fetching competency trend:", err);
                document.getElementById('competencyChart').classList.add('hidden');
                document.getElementById('competencyModalEmptyState').textContent = 'Įvyko klaida gaunant duomenis.';
                document.getElementById('competencyModalEmptyState').classList.remove('hidden');
            });
    }

    function closeCompetencyModal() {
        document.getElementById('competencyModal').classList.add('hidden');
    }
</script>
{% endblock scripts %}"""

    content = content.replace("</main>\n{% endblock %}", modal_and_scripts)

    with open('templates/results.html', 'w', encoding='utf-8') as f:
        f.write(content)

    print("SUCCESS")

if __name__ == "__main__":
    patch_results_html()
