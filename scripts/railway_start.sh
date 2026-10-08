#!/bin/sh
set -eu
mkdir -p "${ADVERTISEMENT_ROOT:-/app/assets/advertisements}"
exec gunicorn pulse_hms.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
