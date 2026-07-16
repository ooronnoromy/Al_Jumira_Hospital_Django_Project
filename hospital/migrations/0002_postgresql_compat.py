from django.db import migrations

def create_compat_functions(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    statements = [
        r"""
        CREATE OR REPLACE FUNCTION hms_date(value text)
        RETURNS date LANGUAGE sql IMMUTABLE AS $$
            SELECT NULLIF(value, '')::date
        $$
        """,
        r"""
        CREATE OR REPLACE FUNCTION hms_datetime(value text)
        RETURNS timestamp LANGUAGE sql IMMUTABLE AS $$
            SELECT NULLIF(value, '')::timestamp
        $$
        """,
        r"""
        CREATE OR REPLACE FUNCTION hms_datetime(value text, modifier text)
        RETURNS text LANGUAGE sql STABLE AS $$
            SELECT CASE
                WHEN lower(value) = 'now' THEN to_char(CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Dhaka', 'YYYY-MM-DD HH24:MI:SS')
                ELSE value
            END
        $$
        """,
        r"""
        CREATE OR REPLACE FUNCTION hms_strftime(format text, value text)
        RETURNS text LANGUAGE sql IMMUTABLE AS $$
            SELECT CASE
                WHEN format = '%Y-%m' THEN substring(COALESCE(value, '') from 1 for 7)
                ELSE COALESCE(value, '')
            END
        $$
        """,
    ]
    with schema_editor.connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)

def drop_compat_functions(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('DROP FUNCTION IF EXISTS hms_strftime(text, text)')
        cursor.execute('DROP FUNCTION IF EXISTS hms_datetime(text, text)')
        cursor.execute('DROP FUNCTION IF EXISTS hms_datetime(text)')
        cursor.execute('DROP FUNCTION IF EXISTS hms_date(text)')

class Migration(migrations.Migration):
    dependencies = [('hospital', '0001_initial')]
    operations = [migrations.RunPython(create_compat_functions, drop_compat_functions)]
