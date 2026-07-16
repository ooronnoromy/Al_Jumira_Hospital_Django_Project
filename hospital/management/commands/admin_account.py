from getpass import getpass

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from werkzeug.security import generate_password_hash

from hospital.models import Admin


class Command(BaseCommand):
    help = 'Create, rename, or reset a PostgreSQL-backed administrator account.'

    def add_arguments(self, parser):
        parser.add_argument('username', help='Existing administrator username, or a new username to create.')
        parser.add_argument('--new-username', help='Rename an existing administrator account.')
        parser.add_argument('--email', help='Set or replace the administrator email address.')

    def handle(self, *args, **options):
        username = options['username'].strip()
        new_username = (options.get('new_username') or username).strip()
        email = (options.get('email') or '').strip() or None

        if not username or not new_username:
            raise CommandError('Username cannot be empty.')

        password = getpass('New password: ')
        confirmation = getpass('Confirm password: ')
        if password != confirmation:
            raise CommandError('Passwords do not match.')
        if len(password) < 8:
            raise CommandError('Password must contain at least 8 characters.')

        try:
            with transaction.atomic():
                account = Admin.objects.filter(username=username).first()
                created = account is None
                if created:
                    account = Admin(username=new_username)
                account.username = new_username
                account.password = generate_password_hash(password)
                if email is not None or created:
                    account.email = email
                account.save()
        except IntegrityError as exc:
            raise CommandError('That username or email is already used by another administrator.') from exc

        action = 'created' if created else 'updated'
        self.stdout.write(self.style.SUCCESS(f'Administrator {new_username!r} {action} in PostgreSQL.'))
