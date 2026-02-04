#!/usr/bin/env python3
"""
Build self-contained docs/index.html for GitHub Pages deployment
Inlines all CSS, JS, and data files
"""

import json
import re
from pathlib import Path

def read_file(path):
    """Read file content"""
    return Path(path).read_text(encoding='utf-8')

def inline_css_files(html, web_dir):
    """Inline CSS files"""
    css_pattern = r'<link[^>]+href=["\']css/([^"\']+\.css)["\'][^>]*>'
    
    def replace_css(match):
        css_file = match.group(1)
        css_path = web_dir / 'css' / css_file
        if css_path.exists():
            css_content = read_file(css_path)
            return f'<style>\n{css_content}\n</style>'
        return match.group(0)
    
    return re.sub(css_pattern, replace_css, html)

def inline_js_files(html, web_dir, docs_dir):
    """Inline JavaScript files"""
    js_pattern = r'<script[^>]+src=["\']js/([^"\']+\.js)["\'][^>]*></script>'
    
    def replace_js(match):
        js_file = match.group(1)
        js_path = web_dir / 'js' / js_file
        if js_path.exists():
            js_content = read_file(js_path)
            return f'<script>\n{js_content}\n</script>'
        return match.group(0)
    
    html = re.sub(js_pattern, replace_js, html)
    
    # Add static data override
    static_data_js = docs_dir / 'js' / 'static-data.js'
    if static_data_js.exists():
        static_content = read_file(static_data_js)
        
        # Inline the data files
        listings_data = read_file(docs_dir / 'js' / 'data-listings.json')
        stats_data = read_file(docs_dir / 'js' / 'data-stats.json')
        
        # Replace fetch calls with inline data
        static_content = static_content.replace(
            "const STATIC_LISTINGS = fetch('js/data-listings.json').then(r => r.json());",
            f"const STATIC_LISTINGS = Promise.resolve({listings_data});"
        )
        static_content = static_content.replace(
            "const STATIC_STATS = fetch('js/data-stats.json').then(r => r.json());",
            f"const STATIC_STATS = Promise.resolve({stats_data});"
        )
        
        # Insert static data script before the closing body tag
        html = html.replace('</body>', f'<script>\n{static_content}\n</script>\n</body>')
    
    return html

def build_docs():
    """Build self-contained docs/index.html"""
    base_dir = Path(__file__).parent
    web_dir = base_dir / 'web'
    docs_dir = base_dir / 'docs'
    
    print('Building self-contained docs/index.html...')
    
    # Read the base HTML
    html = read_file(web_dir / 'index.html')
    
    # Inline CSS files
    print('Inlining CSS...')
    html = inline_css_files(html, web_dir)
    
    # Inline JS files
    print('Inlining JavaScript...')
    html = inline_js_files(html, web_dir, docs_dir)
    
    # Add a comment at the top
    html = '<!-- Auto-generated self-contained file for GitHub Pages - DO NOT EDIT DIRECTLY -->\n' + html
    
    # Write output
    output_path = docs_dir / 'index.html'
    output_path.write_text(html, encoding='utf-8')
    
    # Get file size
    size_kb = output_path.stat().st_size / 1024
    print(f'✓ Built docs/index.html ({size_kb:.1f} KB)')
    
    return True

if __name__ == '__main__':
    try:
        build_docs()
        print('Build complete!')
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        exit(1)
