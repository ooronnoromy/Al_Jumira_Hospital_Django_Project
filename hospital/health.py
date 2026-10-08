from django.db import DatabaseError, connection, transaction
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@transaction.non_atomic_requests
@require_GET
def healthcheck(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except DatabaseError:
        return JsonResponse({'status': 'unavailable'}, status=503)
    return JsonResponse({'status': 'ok'})
