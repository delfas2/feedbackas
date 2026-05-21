#!/bin/bash
# Compute SRI hashes for CDN resources

compute_sri() {
    local url="$1"
    local label="$2"
    local hash=$(curl -sL "$url" | openssl dgst -sha384 -binary | openssl base64 -A)
    echo "$label"
    echo "  URL: $url"
    echo "  integrity=\"sha384-$hash\""
    echo ""
}

# Lucide 0.460.0
compute_sri "https://unpkg.com/lucide@0.460.0" "Lucide Icons 0.460.0"

# Chart.js 4.4.7
compute_sri "https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js" "Chart.js 4.4.7"

# TinyMCE 6.8.2
compute_sri "https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.8.2/tinymce.min.js" "TinyMCE 6.8.2"

# Tom Select 2.4.1 CSS
compute_sri "https://cdn.jsdelivr.net/npm/tom-select@2.4.1/dist/css/tom-select.css" "Tom Select 2.4.1 CSS"

# Tom Select 2.4.1 JS
compute_sri "https://cdn.jsdelivr.net/npm/tom-select@2.4.1/dist/js/tom-select.complete.min.js" "Tom Select 2.4.1 JS"

# React 18 production
compute_sri "https://unpkg.com/react@18/umd/react.production.min.js" "React 18 Production"

# React DOM 18 production
compute_sri "https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" "React DOM 18 Production"

# Babel standalone
compute_sri "https://unpkg.com/@babel/standalone/babel.min.js" "Babel Standalone"

# Chart.js 4.4.2 (for billing_overview.html)
compute_sri "https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js" "Chart.js 4.4.2"
