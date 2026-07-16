from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


CSRF_EXPIRED_MESSAGE = 'Your form security token expired. Please submit the form again.'


def csrf_failure(request, reason=''):
    """Recover safely from stale forms while keeping CSRF enforcement enabled."""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'success': False, 'error': CSRF_EXPIRED_MESSAGE}, status=403)

    referrer = request.META.get('HTTP_REFERER', '')
    if url_has_allowed_host_and_scheme(
        referrer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        parts = urlsplit(referrer)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query['error'] = CSRF_EXPIRED_MESSAGE
        return redirect(urlunsplit(('', '', parts.path, urlencode(query), '')))

    return redirect(f"{reverse('login')}?{urlencode({'error': CSRF_EXPIRED_MESSAGE})}")
