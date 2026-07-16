#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg import sql

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / '.env')

TABLES = [
    'admins', 'users', 'app_migrations', 'doctors', 'services', 'patients',
    'user_permissions', 'doctor_fee_due_collections', 'patient_visit_returns',
    'test_orders', 'doctor_prescriptions', 'doctor_prescription_drafts',
    'test_bills', 'test_bill_items', 'test_bill_returns', 'bills', 'bill_items',
    'admissions', 'discharge_bills', 'duty_records', 'daily_expenses',
    'expense_categories', 'patient_queue_state', 'medicine_transactions',
    'medicine_sales', 'medicine_sale_items', 'medicine_returns',
    'medicine_return_items', 'logs',
]

def pg_connect():
    return psycopg.connect(
        dbname=os.getenv('POSTGRES_DB', 'hospital_db'),
        user=os.getenv('POSTGRES_USER', 'hospital_user'),
        password=os.getenv('POSTGRES_PASSWORD', 'change-me'),
        host=os.getenv('POSTGRES_HOST', '127.0.0.1'),
        port=os.getenv('POSTGRES_PORT', '5432'),
    )

def main():
    parser = argparse.ArgumentParser(description='Copy the original hospital.db data into PostgreSQL.')
    parser.add_argument('sqlite_db', type=Path)
    parser.add_argument('--clear', action='store_true', help='Clear destination hospital tables first.')
    args = parser.parse_args()
    if not args.sqlite_db.is_file():
        raise SystemExit(f'File not found: {args.sqlite_db}')

    source = sqlite3.connect(args.sqlite_db)
    source.row_factory = sqlite3.Row
    target = None
    copied = 0
    try:
        target = pg_connect()
        with target.transaction():
            with target.cursor() as cur:
                cur.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                )
                target_tables = {row[0] for row in cur.fetchall()}
                missing_tables = [table for table in TABLES if table not in target_tables]
                if missing_tables:
                    raise SystemExit(
                        'PostgreSQL schema is not ready. Run `python manage.py migrate` first. '
                        f'Missing tables: {", ".join(missing_tables)}'
                    )

                if args.clear:
                    cur.execute(sql.SQL('TRUNCATE {} RESTART IDENTITY CASCADE').format(
                        sql.SQL(', ').join(sql.Identifier(t) for t in reversed(TABLES))
                    ))

                for table in TABLES:
                    exists = source.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
                    ).fetchone()
                    if not exists:
                        print(f'Skip {table}: not present in SQLite')
                        continue
                    source_columns = [row['name'] for row in source.execute(f'PRAGMA table_info("{table}")')]
                    cur.execute(
                        "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position",
                        (table,),
                    )
                    target_columns = {row[0] for row in cur.fetchall()}
                    columns = [c for c in source_columns if c in target_columns]
                    rows = source.execute(
                        f'SELECT {", ".join(chr(34)+c+chr(34) for c in columns)} FROM "{table}"'
                    ).fetchall()
                    if not rows:
                        print(f'{table}: 0 rows')
                        continue
                    insert_sql = sql.SQL('INSERT INTO {} ({}) VALUES ({}) ON CONFLICT DO NOTHING').format(
                        sql.Identifier(table),
                        sql.SQL(', ').join(sql.Identifier(c) for c in columns),
                        sql.SQL(', ').join(sql.Placeholder() for _ in columns),
                    )
                    cur.executemany(insert_sql, [tuple(row[c] for c in columns) for row in rows])
                    copied += len(rows)
                    print(f'{table}: {len(rows)} rows')

                for table in TABLES:
                    if table == 'app_migrations':
                        continue
                    cur.execute('SELECT pg_get_serial_sequence(%s, %s)', (table, 'id'))
                    sequence = cur.fetchone()[0]
                    if sequence:
                        cur.execute(
                            sql.SQL('SELECT MAX(id) FROM {}').format(sql.Identifier(table))
                        )
                        max_id = cur.fetchone()[0]
                        # PostgreSQL's third setval argument controls whether the
                        # next nextval() returns this value or increments it first.
                        # Empty tables must therefore use is_called=false so their
                        # first generated primary key remains 1.
                        cur.execute(
                            'SELECT setval(%s, %s, %s)',
                            (sequence, max_id or 1, max_id is not None),
                        )
        print(f'Finished. Considered {copied} source rows.')
    finally:
        source.close()
        if target is not None:
            target.close()

if __name__ == '__main__':
    main()
