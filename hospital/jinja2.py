from jinja2 import Environment
from django.templatetags.static import static
from .compat import request, session, url_for

def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'url_for': url_for,
        'request': request,
        'session': session,
        'static': static,
    })
    try:
        from . import legacy_views
        env.globals.update(legacy_views.inject_permission_helpers())
    except Exception:
        pass
    return env
