from __future__ import annotations

import mimetypes
import os
import re
import threading
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db import connection, transaction
from django.db import Error as DjangoDBError
from django.db import IntegrityError, OperationalError
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import redirect as django_redirect, render as django_render
from django.urls import NoReverseMatch, reverse
from django.utils._os import safe_join
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

_local = threading.local()

ENDPOINT_PARAMS = {'register': [], 'login': [], 'logout': [], 'assets': ['filename'], 'admin_portal': [], 'logs': [], 'follow_up_dashboard': [], 'duty_management_dashboard': [], 'dashboard': [], 'patient_reports': [], 'patient_reports_print': [], 'daily_expenses': [], 'all_transation': [], 'all_transation_print': [], 'daily_expenses_print': [], 'delete_daily_expense': ['expense_id'], 'pathology_dashboard': [], 'update_pathology_status': ['test_bill_id'], 'save_pathology_result': ['test_item_id'], 'pathology_result_print': ['test_item_id'], 'medicine_stock_dashboard': [], 'medicine_stock_movements': ['movement_type'], 'medicine_sales': [], 'save_medicine_sale': [], 'medicine_sales_print': ['sale_id'], 'medicine_return': [], 'medicine_sales_list': [], 'medicine_sales_list_print': [], 'medicine_monthly_report': [], 'delete_medicine_monthly_day_sales': [], 'delete_medicine_monthly_product_sales': [], 'delete_medicine_sale': ['sale_id'], 'edit_medicine_transaction': ['transaction_id'], 'delete_medicine_transaction': ['transaction_id'], 'delete_medicine_balance': [], 'patient': [], 'add_patient': [], 'delete_patient': ['patient_id'], 'visit_return': [], 'admissions': [], 'inpatient_dashboard': [], 'inpatient_patient_workspace': ['admission_id'], 'add_inpatient_round': ['admission_id'], 'add_inpatient_medication': ['admission_id'], 'add_inpatient_test': ['admission_id'], 'admission_details': ['admission_id'], 'admission_form_print': ['admission_id'], 'search_old_admitted_patient': [], 'concern_paper': ['admission_id'], 'due_collection_hub': [], 'doctor_fee_due_collection': [], 'collect_doctor_fee_due': ['patient_id'], 'discharge_bill': [], 'discharge_bill_print': ['admission_id'], 'saved_discharge_bill_print': ['bill_id'], 'discharge_due_details': ['bill_id'], 'collect_discharge_due': ['bill_id'], 'discharge_due_collection': [], 'discharge_patients_list': [], 'discharge_admission': ['admission_id'], 'registered_users': [], 'update_account': [], 'update_user_permissions': [], 'delete_user': [], 'doctors': [], 'doctor_prescription': [], 'patients_serial': [], 'hospital_advertisement': [], 'upload_hospital_advertisement': [], 'patients_serial_status': [], 'advance_patient_serial': [], 'doctor_prescription_print': [], 'save_doctor_prescription_draft': [], 'get_doctor_prescription_draft': ['patient_id'], 'saved_doctor_prescription': ['prescription_id'], 'doctor_prescription_list': [], 'duty_management': [], 'patients_registration': [], 'patients_info': [], 'edit_patient_profile': ['patient_id'], 'patient_details_bill': ['patient_id'], 'patient_visits_print': ['patient_id'], 'patient_pathology_print': ['patient_id'], 'search_registered_patient': [], 'ticket_print': ['patient_id'], 'tickets': [], 'add_doctor': [], 'edit_doctor': ['doctor_id'], 'delete_doctor': ['doctor_id'], 'services': [], 'add_service': [], 'edit_service': ['service_id'], 'delete_service': ['service_id'], 'test_billing': [], 'patient_prescribed_tests': ['patient_id'], 'test_bill_details': ['test_bill_id'], 'test_bill_print': ['test_bill_id'], 'test_return': [], 'test_due_details': ['test_bill_id'], 'collect_test_due': ['test_bill_id'], 'due': [], 'test_due_collection': [], 'tests': []}
ID_TABLES = {
    'users', 'admins', 'patients', 'user_permissions', 'doctor_fee_due_collections',
    'patient_visit_returns', 'doctors', 'services', 'test_orders', 'doctor_prescriptions',
    'doctor_prescription_drafts', 'test_bills', 'test_bill_items', 'test_bill_returns',
    'bills', 'bill_items', 'admissions', 'inpatient_rounds', 'inpatient_medications',
    'inpatient_test_orders', 'discharge_bills', 'duty_records',
    'daily_expenses', 'expense_categories', 'patient_queue_state', 'medicine_transactions',
    'medicine_sales', 'medicine_sale_items', 'medicine_returns', 'medicine_return_items', 'logs',
}


def set_current_request(value):
    _local.request = value


def get_current_request():
    value = getattr(_local, 'request', None)
    if value is None:
        raise RuntimeError('No active Django request is available.')
    return value


class UploadedFileAdapter:
    def __init__(self, uploaded):
        self._uploaded = uploaded
        self.filename = uploaded.name
        self.name = uploaded.name
        self.content_type = uploaded.content_type

    def save(self, destination):
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('wb') as target:
            for chunk in self._uploaded.chunks():
                target.write(chunk)

    def __getattr__(self, item):
        return getattr(self._uploaded, item)


class FilesProxy:
    def get(self, key, default=None):
        value = get_current_request().FILES.get(key)
        return UploadedFileAdapter(value) if value is not None else default

    def getlist(self, key):
        return [UploadedFileAdapter(v) for v in get_current_request().FILES.getlist(key)]


class RequestProxy:
    @property
    def args(self):
        return get_current_request().GET

    @property
    def form(self):
        return get_current_request().POST

    @property
    def files(self):
        return FilesProxy()

    @property
    def method(self):
        return get_current_request().method

    @property
    def headers(self):
        return get_current_request().headers

    @property
    def content_length(self):
        raw = get_current_request().META.get('CONTENT_LENGTH')
        try:
            return int(raw) if raw else None
        except (TypeError, ValueError):
            return None

    @property
    def is_json(self):
        return (get_current_request().content_type or '').split(';', 1)[0].lower() == 'application/json'

    @property
    def endpoint(self):
        match = getattr(get_current_request(), 'resolver_match', None)
        return match.url_name if match else None

    def get_json(self, silent=False):
        try:
            import json
            body = get_current_request().body.decode(get_current_request().encoding or 'utf-8')
            return json.loads(body) if body else None
        except Exception:
            if silent:
                return None
            raise


class SessionProxy:
    def _session(self):
        return get_current_request().session

    def get(self, key, default=None):
        return self._session().get(key, default)

    def clear(self):
        return self._session().flush()

    def pop(self, key, default=None):
        return self._session().pop(key, default)

    def __getitem__(self, key):
        return self._session()[key]

    def __setitem__(self, key, value):
        self._session()[key] = value

    def __contains__(self, key):
        return key in self._session()

    def __iter__(self):
        return iter(self._session())


request = RequestProxy()
session = SessionProxy()


def _query_string(values):
    items = []
    for key, value in values.items():
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            items.extend((key, item) for item in value)
        else:
            items.append((key, value))
    return urlencode(items, doseq=True)


def url_for(endpoint, **values):
    endpoint = endpoint.split('.', 1)[-1]
    if endpoint == 'static':
        filename = str(values.get('filename', '')).lstrip('/')
        return staticfiles_storage.url(filename)
    path_keys = ENDPOINT_PARAMS.get(endpoint, [])
    path_values = {key: values.pop(key) for key in list(values) if key in path_keys}
    try:
        url = reverse(endpoint, kwargs=path_values or None)
    except NoReverseMatch:
        # Helps template migration when a non-path value was supplied to Flask's url_for.
        url = reverse(endpoint)
    query = _query_string(values)
    return f'{url}?{query}' if query else url


def render_template(template_name, **context):
    try:
        from . import legacy_views
        context = {**legacy_views.inject_permission_helpers(), **context}
    except Exception:
        pass
    return django_render(get_current_request(), template_name, context=context, using='jinja2')


def redirect(location, *args, **kwargs):
    return django_redirect(location, *args, **kwargs)


def jsonify(*args, **kwargs):
    if args and kwargs:
        raise TypeError('Use positional or keyword JSON data, not both.')
    if len(args) == 1:
        data = args[0]
    elif len(args) > 1:
        data = list(args)
    else:
        data = kwargs
    return JsonResponse(data, safe=isinstance(data, dict))


def send_from_directory(directory, filename):
    base = Path(directory)
    if not base.is_absolute():
        base = Path(settings.BASE_DIR) / base
    full_path = Path(safe_join(str(base), filename))
    if not full_path.is_file():
        return HttpResponse('File not found', status=404)
    content_type, _ = mimetypes.guess_type(str(full_path))
    return FileResponse(full_path.open('rb'), content_type=content_type or 'application/octet-stream')


class ResultCursor:
    def __init__(self, rows=None, *, lastrowid=None, rowcount=-1):
        self._rows = list(rows or [])
        self._index = 0
        self.lastrowid = lastrowid
        self.rowcount = rowcount

    def fetchone(self):
        if self._index >= len(self._rows):
            return None
        row = self._rows[self._index]
        self._index += 1
        return row

    def fetchall(self):
        rows = self._rows[self._index:]
        self._index = len(self._rows)
        return rows

    def __iter__(self):
        return iter(self.fetchall())


class DatabaseAdapter:
    _numeric_empty = re.compile(
        r"COALESCE\(\s*((?:[A-Za-z_]\w*\.)?(?:id|[A-Za-z_]\w*_id|ticket_no|current_ticket_no))\s*,\s*''\s*\)",
        re.IGNORECASE,
    )
    _cast_numeric_empty = re.compile(
        r"CAST\(\s*COALESCE\(\s*((?:[A-Za-z_]\w*\.)?(?:id|[A-Za-z_]\w*_id|ticket_no|current_ticket_no))\s*,\s*''\s*\)\s+AS\s+TEXT\s*\)",
        re.IGNORECASE,
    )

    def _translate(self, sql):
        sql = str(sql).strip()
        # Django/psycopg uses percent-style parameter handling. Escape every
        # literal percent from the legacy SQLite SQL before creating the %s
        # placeholders, otherwise LIKE patterns such as 'Patient created:%'
        # are parsed as invalid parameters whenever a query has arguments.
        sql = sql.replace('%', '%%')
        # Django database cursors use %s placeholders for every backend,
        # including SQLite during local smoke tests.
        sql = sql.replace('?', '%s')
        if connection.vendor != 'postgresql':
            return sql, False

        ignored = bool(re.search(r'\bINSERT\s+OR\s+IGNORE\b', sql, flags=re.IGNORECASE))
        sql = re.sub(r'\bINSERT\s+OR\s+IGNORE\b', 'INSERT', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\s+COLLATE\s+NOCASE\b', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bdatetime\s*\(', 'hms_datetime(', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bstrftime\s*\(', 'hms_strftime(', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bdate\s*\(', 'hms_date(', sql, flags=re.IGNORECASE)
        # SQLite's two-argument GROUP_CONCAT maps directly to PostgreSQL's
        # STRING_AGG for the simple text columns used by the legacy reports.
        sql = re.sub(
            r'\bGROUP_CONCAT\s*\(\s*([A-Za-z_]\w*\.[A-Za-z_]\w*)\s*,',
            r'STRING_AGG(\1,',
            sql,
            flags=re.IGNORECASE,
        )
        sql = self._cast_numeric_empty.sub(r"COALESCE(CAST(\1 AS TEXT), '')", sql)
        sql = self._numeric_empty.sub(r"COALESCE(CAST(\1 AS TEXT), '')", sql)
        sql = sql.replace(
            'MAX(COALESCE(doctor_fee, 0) - COALESCE(doctor_paid_amount, 0), 0)',
            'GREATEST(COALESCE(doctor_fee, 0) - COALESCE(doctor_paid_amount, 0), 0)',
        )
        sql = sql.rstrip().rstrip(';')
        if ignored:
            sql += ' ON CONFLICT DO NOTHING'
        return sql, ignored

    def execute(self, sql, params=()):
        translated, _ = self._translate(sql)
        return_id = False
        if connection.vendor == 'postgresql':
            match = re.match(r'\s*INSERT\s+INTO\s+([A-Za-z_]\w*)\b', translated, flags=re.IGNORECASE)
            if match and match.group(1).lower() in ID_TABLES and not re.search(r'\bRETURNING\b', translated, flags=re.IGNORECASE):
                translated += ' RETURNING id'
                return_id = True

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(translated, tuple(params or ()))
                rows = cursor.fetchall() if cursor.description else []
                rowcount = cursor.rowcount
                lastrowid = None
                if return_id and rows:
                    lastrowid = rows[0][0]
                elif connection.vendor == 'sqlite':
                    lastrowid = getattr(cursor, 'lastrowid', None)
                return ResultCursor(rows, lastrowid=lastrowid, rowcount=rowcount)

    def table_exists(self, table_name):
        """Return whether a table exists using Django's backend-neutral API."""
        return str(table_name) in connection.introspection.table_names()

    def commit(self):
        # Django's ATOMIC_REQUESTS and nested savepoints manage commits.
        return None

    def rollback(self):
        # Each execute() uses a savepoint, so failed statements are already rolled back.
        return None


db = DatabaseAdapter()
sqlite3 = SimpleNamespace(
    Error=DjangoDBError,
    DatabaseError=DjangoDBError,
    IntegrityError=IntegrityError,
    OperationalError=OperationalError,
)


def normalize_response(result):
    status = None
    headers = None
    if isinstance(result, tuple):
        if len(result) == 2:
            result, status = result
        elif len(result) == 3:
            result, status, headers = result
    if isinstance(result, HttpResponse):
        response = result
        if status is not None:
            response.status_code = int(status)
    elif isinstance(result, (dict, list)):
        response = JsonResponse(result, safe=isinstance(result, dict), status=int(status or 200))
    elif result is None:
        response = HttpResponse('', status=int(status or 204))
    else:
        response = HttpResponse(result, status=int(status or 200))
    if headers:
        for key, value in dict(headers).items():
            response[key] = value
    return response


def legacy_view(func):
    def wrapped(django_request, *args, **kwargs):
        set_current_request(django_request)
        # Reuse the Flask before_request permission logic.
        from . import legacy_views
        permission_response = legacy_views.enforce_user_page_permissions()
        if permission_response is not None:
            return normalize_response(permission_response)
        return normalize_response(func(*args, **kwargs))

    wrapped.__name__ = func.__name__
    wrapped.__doc__ = func.__doc__
    return wrapped
