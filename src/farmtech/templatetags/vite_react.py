from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def vite_react_app(app_name):
    """
    Load a Vite React app with proper dev/prod handling.

    Usage in template:
    {% load vite_react %}
    {% vite_react_app 'farmtech-uploader' %}

    In dev mode: Loads from Vite dev server (localhost:8081)
    In prod mode: Loads from static files (dist/)

    Translations are handled by react-i18next, loading from:
    - client/public/locales/{lang}/{namespace}.json
    """

    # Determine if we're in development mode
    is_dev = settings.DEBUG

    if is_dev:
        # Development mode: Use Vite dev server
        html = f'''
<!-- Vite React App: {app_name} (DEV MODE) -->
<script type="module">
  import RefreshRuntime from 'http://localhost:8081/@react-refresh'
  RefreshRuntime.injectIntoGlobalHook(window)
  window.$RefreshReg$ = () => {{}}
  window.$RefreshSig$ = () => (type) => type
  window.__vite_plugin_react_preamble_installed__ = true
</script>
<script type="module" src="http://localhost:8081/@vite/client"></script>
<script type="module" src="http://localhost:8081/js/apps/{app_name}.jsx"></script>
'''
    else:
        # Production mode: Use built static files TODO: da testare e da trovare un modo per rendere automatica la build
        from django.templatetags.static import static
        html = f'''
<!-- Vite React App: {app_name} (PRODUCTION MODE) -->
<link rel="stylesheet" href="{static('dist/style/react-apps.css')}">
<script type="module" src="{static(f'dist/js/{app_name}.js')}"></script>
'''

    return mark_safe(html)
