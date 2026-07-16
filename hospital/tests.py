import re
from django.test import TestCase
from django.test import Client
from django.urls import reverse
from django.contrib.staticfiles import finders
from django.contrib import admin as django_admin
from django.apps import apps
from django.conf import settings
from django.db import connection
from werkzeug.security import check_password_hash, generate_password_hash
from hospital.urls import urlpatterns
from hospital.models import (
    Admin, Admission, DischargeBill, Doctor, DoctorPrescription, MedicineSale,
    InpatientMedication, InpatientRound, InpatientTestOrder, MedicineTransaction,
    Patient, Service, TestBill, TestBillItem, User,
)

TEST_ADMIN_USERNAME = 'database-admin'
TEST_ADMIN_PASSWORD = 'database-test-password'


class DjangoAdminRegistrationTests(TestCase):
    def test_all_hospital_models_are_registered(self):
        hospital_models = apps.get_app_config('hospital').get_models()

        for model in hospital_models:
            with self.subTest(model=model.__name__):
                self.assertTrue(django_admin.site.is_registered(model))


def create_test_admin():
    return Admin.objects.create(
        username=TEST_ADMIN_USERNAME,
        password=generate_password_hash(TEST_ADMIN_PASSWORD),
        email='database-admin@example.com',
    )

class SmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = create_test_admin()

    def test_login_page(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/static/css/login.css"')
        self.assertIsNotNone(finders.find('css/login.css'))

    def test_database_admin_login(self):
        response = self.client.post(reverse('login'), {
            'username': TEST_ADMIN_USERNAME,
            'password': TEST_ADMIN_PASSWORD,
        })
        self.assertEqual(response.status_code, 302)

    def test_environment_root_admin_is_not_accepted(self):
        response = self.client.post(reverse('login'), {
            'username': 'admin',
            'password': 'change-me-now',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password.')

    def test_login_form_is_csrf_protected_and_usable(self):
        csrf_client = Client(enforce_csrf_checks=True)
        get_response = csrf_client.get(reverse('login'))
        token = get_response.cookies['csrftoken'].value

        rejected = Client(enforce_csrf_checks=True).post(reverse('login'), {
            'username': TEST_ADMIN_USERNAME,
            'password': TEST_ADMIN_PASSWORD,
        })
        accepted = csrf_client.post(reverse('login'), {
            'csrfmiddlewaretoken': token,
            'username': TEST_ADMIN_USERNAME,
            'password': TEST_ADMIN_PASSWORD,
        })

        self.assertEqual(rejected.status_code, 302)
        self.assertEqual(accepted.status_code, 302)

    def test_csrf_failure_returns_user_to_fresh_form(self):
        csrf_client = Client(enforce_csrf_checks=True)
        session = csrf_client.session
        session['user_id'] = self.admin.id
        session['role'] = 'admin'
        session.save()
        form_response = csrf_client.get(reverse('add_doctor'))
        stale_token = re.search(
            r'name="csrfmiddlewaretoken" value="([^"]+)"',
            form_response.content.decode(),
        ).group(1)
        csrf_client.cookies['csrftoken'] = 'a' * 32

        response = csrf_client.post(
            reverse('add_doctor'),
            {'csrfmiddlewaretoken': stale_token},
            HTTP_REFERER='http://testserver/add_doctor',
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('/add_doctor?error=', response['Location'])

    def test_add_doctor_with_fresh_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        login_page = csrf_client.get(reverse('login'))
        login_token = re.search(
            r'name="csrfmiddlewaretoken" value="([^"]+)"',
            login_page.content.decode(),
        ).group(1)
        login_response = csrf_client.post(reverse('login'), {
            'csrfmiddlewaretoken': login_token,
            'username': TEST_ADMIN_USERNAME,
            'password': TEST_ADMIN_PASSWORD,
        })
        self.assertEqual(login_response.status_code, 302)

        doctor_page = csrf_client.get(reverse('add_doctor'))
        doctor_token = re.search(
            r'name="csrfmiddlewaretoken" value="([^"]+)"',
            doctor_page.content.decode(),
        ).group(1)
        response = csrf_client.post(reverse('add_doctor'), {
            'csrfmiddlewaretoken': doctor_token,
            'name': 'CSRF Test Doctor', 'phone': '01400000000',
            'email': 'csrf-doctor@example.com', 'specialization': 'Medicine',
            'designation': 'Consultant', 'department': 'Medicine',
            'license_number': 'CSRF-1', 'availability': 'Daily',
            'experience': '2', 'room_number': '104', 'consultation_fee': '500',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Doctor.objects.filter(name='CSRF Test Doctor', is_active=1).exists())

    def test_all_patients_button_opens_all_patients_list(self):
        session = self.client.session
        session['user_id'] = self.admin.id
        session['role'] = 'admin'
        session.save()

        all_patients_url = f"{reverse('patients_registration')}?view=all"
        response = self.client.get(all_patients_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h2><i class="fas fa-list"></i> All Patients List</h2>', html=True)
        self.assertContains(response, f'href="{all_patients_url}"')
        self.assertContains(response, f'data-all-url="{all_patients_url}"')
        self.assertContains(response, 'onclick="window.location.href=this.dataset.allUrl; return false;"')

    def test_key_report_pages_for_database_admin(self):
        session = self.client.session
        session['user_id'] = self.admin.id
        session['role'] = 'admin'
        session.save()
        for url in (
            reverse('admin_portal'),
            reverse('follow_up_dashboard'),
            reverse('patient_reports'),
            reverse('daily_expenses'),
            reverse('all_transation'),
            reverse('all_transation_print'),
            reverse('pathology_dashboard'),
            reverse('medicine_stock_dashboard'),
            reverse('medicine_sales'),
            reverse('medicine_monthly_report'),
            reverse('patients_registration'),
            reverse('test_due_collection'),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_all_static_routes_do_not_crash_for_database_admin(self):
        session = self.client.session
        session['user_id'] = self.admin.id
        session['role'] = 'admin'
        session.save()

        for pattern in urlpatterns:
            route = str(pattern.pattern)
            if '<' in route:
                continue
            url = f'/{route}'
            with self.subTest(route=route, name=pattern.name):
                response = self.client.get(url)
                self.assertLess(response.status_code, 500)
                if response.status_code == 200 and response.get('Content-Type', '').startswith('text/html'):
                    self.assertNotContains(response, 'href="#"')
                    self.assertNotContains(response, 'action="#"')
                    self.assertNotContains(response, 'data-list-url="#"')
                    body = response.content.decode(response.charset or 'utf-8')
                    static_paths = re.findall(r'(?:href|src)="/static/([^"?]+)', body)
                    for static_path in static_paths:
                        self.assertIsNotNone(
                            finders.find(static_path),
                            f'Missing static asset {static_path!r} rendered by {url!r}',
                        )
                    post_forms = re.findall(
                        r'(?is)<form\b(?=[^>]*\bmethod=["\']post["\'])[^>]*>.*?</form>',
                        body,
                    )
                    for form in post_forms:
                        self.assertIn('name="csrfmiddlewaretoken"', form)

    def test_required_hospital_assets_exist(self):
        for filename in ('logo.png', 'background.png'):
            with self.subTest(filename=filename):
                self.assertTrue((settings.BASE_DIR / 'assets' / filename).is_file())

    def test_admin_can_edit_admin_and_employee_information(self):
        session = self.client.session
        session['user_id'] = self.admin.id
        session['role'] = 'admin'
        session.save()

        admin_response = self.client.post(reverse('update_account'), {
            'account_type': 'admin',
            'account_id': str(self.admin.id),
            'username': 'renamed-admin',
            'email': 'renamed-admin@example.com',
            'new_password': 'new-database-password',
            'confirm_password': 'new-database-password',
        })
        self.assertEqual(admin_response.status_code, 302)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.username, 'renamed-admin')
        self.assertEqual(self.admin.email, 'renamed-admin@example.com')
        self.assertTrue(check_password_hash(self.admin.password, 'new-database-password'))

        original_user_hash = generate_password_hash('employee-password')
        employee = User.objects.create(
            username='employee', password=original_user_hash,
            email='employee@example.com',
        )
        user_response = self.client.post(reverse('update_account'), {
            'account_type': 'user',
            'account_id': str(employee.id),
            'username': 'renamed-employee',
            'email': 'renamed-employee@example.com',
            'new_password': '',
            'confirm_password': '',
        })
        self.assertEqual(user_response.status_code, 302)
        employee.refresh_from_db()
        self.assertEqual(employee.username, 'renamed-employee')
        self.assertEqual(employee.email, 'renamed-employee@example.com')
        self.assertEqual(employee.password, original_user_hash)


class DataBackedRouteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = create_test_admin()
        cls.patient = Patient.objects.create(
            daily_patient_id=1, name='Route Test Patient', age=30,
            gender='Other', phone='01700000000', dob='1996-01-01',
            blood_group='O+', address='Test Address', created_at='2026-07-15 10:00:00',
            doctor_fee=500, doctor_paid_amount=300, doctor_due_amount=200,
        )
        cls.doctor = Doctor.objects.create(
            name='Route Test Doctor', phone='01800000000', email='doctor@example.com',
            specialization='Medicine', designation='Consultant', department='Medicine',
            license_number='TEST-1', availability='Daily', experience=5,
            room_number='101', consultation_fee=500,
        )
        cls.service = Service.objects.create(
            name='CBC', type='Test', price=500, sample_type='Blood',
            test_category='Hematology', unit='g/dL', reference_ranges='Normal',
        )
        cls.admission = Admission.objects.create(
            patient=cls.patient, doctor=cls.doctor, admission_date='2026-07-15',
            ward='General', bed_number='A-1', reason='Observation',
            created_at='2026-07-15 10:00:00',
        )
        cls.discharge_bill = DischargeBill.objects.create(
            admission=cls.admission, patient=cls.patient, patient_uhid=cls.patient.id,
            bill_no='DB-TEST-1', admission_date='2026-07-15', discharge_date='2026-07-15',
            total_amount=1000, gross_amount=1000, paid_amount=800, due_amount=200,
            created_at='2026-07-15 12:00:00', updated_at='2026-07-15 12:00:00',
        )
        cls.test_bill = TestBill.objects.create(
            invoice_no='TB-TEST-1', patient=cls.patient, subtotal=500,
            total_amount=500, received_amount=300, due_amount=200,
            created_at='2026-07-15 11:00:00',
        )
        cls.test_item = TestBillItem.objects.create(
            test_bill=cls.test_bill, service=cls.service, test_name='CBC', price=500,
        )
        cls.sale = MedicineSale.objects.create(
            invoice_no='MS-TEST-1', customer_name=cls.patient.name,
            grand_total=100, received_amount=100, sale_date='2026-07-15',
            created_at='2026-07-15 11:30:00',
        )
        cls.transaction = MedicineTransaction.objects.create(
            medicine_name='Test Medicine', batch_no='B-1', transaction_type='purchase',
            quantity=10, price=10, transaction_date='2026-07-15',
            created_at='2026-07-15 09:00:00',
        )
        cls.prescription = DoctorPrescription.objects.create(
            prescription_no='RX-TEST-1', prescription_date='2026-07-15',
            patient=cls.patient, doctor=cls.doctor, created_at='2026-07-15 12:30:00',
        )

    def setUp(self):
        session = self.client.session
        session['user_id'] = self.admin.id
        session['role'] = 'admin'
        session.save()

    def test_data_backed_display_routes_do_not_crash(self):
        urls = (
            reverse('admission_details', args=[self.admission.id]),
            reverse('admission_form_print', args=[self.admission.id]),
            reverse('concern_paper', args=[self.admission.id]),
            reverse('discharge_bill_print', args=[self.admission.id]),
            reverse('saved_discharge_bill_print', args=[self.discharge_bill.id]),
            reverse('discharge_due_details', args=[self.discharge_bill.id]),
            reverse('medicine_sales_print', args=[self.sale.id]),
            reverse('medicine_stock_movements', args=['purchase']),
            reverse('pathology_result_print', args=[self.test_item.id]),
            reverse('get_doctor_prescription_draft', args=[self.patient.id]),
            reverse('saved_doctor_prescription', args=[self.prescription.id]),
            reverse('doctor_prescription_list'),
            reverse('patient_details_bill', args=[self.patient.id]),
            reverse('patient_visits_print', args=[self.patient.id]),
            reverse('patient_pathology_print', args=[self.patient.id]),
            reverse('ticket_print', args=[self.patient.id]),
            reverse('patient_prescribed_tests', args=[self.patient.id]),
            reverse('test_bill_details', args=[self.test_bill.id]),
            reverse('test_bill_print', args=[self.test_bill.id]),
            reverse('test_due_details', args=[self.test_bill.id]),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertLess(response.status_code, 500)

    def test_deleting_linked_doctor_preserves_history(self):
        response = self.client.post(reverse('delete_doctor', args=[self.doctor.id]))

        self.assertEqual(response.status_code, 302)
        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.is_active, 0)
        self.assertTrue(Admission.objects.filter(doctor=self.doctor).exists())

    def test_core_registration_and_catalog_workflows(self):
        patient_response = self.client.post(
            f"{reverse('add_patient')}?next=patients_registration",
            {
                'name': 'New Workflow Patient', 'age': '25', 'age_unit': 'Y',
                'gender': 'Other', 'phone': '01900000000', 'blood_group': 'A+',
                'address': 'Workflow Address', 'patient_status': 'NEW',
                'doctor_name': self.doctor.name, 'doctor_designation': self.doctor.designation,
                'referer_name': 'Self', 'save_action': 'register',
            },
        )
        self.assertEqual(patient_response.status_code, 302)
        self.assertTrue(Patient.objects.filter(name='New Workflow Patient').exists())

        doctor_response = self.client.post(reverse('add_doctor'), {
            'name': 'New Workflow Doctor', 'phone': '01600000000',
            'email': 'new-doctor@example.com', 'specialization': 'Surgery',
            'designation': 'Consultant', 'department': 'Surgery',
            'license_number': 'TEST-2', 'availability': 'Daily',
            'experience': '4', 'room_number': '102', 'consultation_fee': '600',
        })
        self.assertEqual(doctor_response.status_code, 302)
        self.assertTrue(Doctor.objects.filter(name='New Workflow Doctor').exists())

        service_response = self.client.post(reverse('add_service'), {
            'name': 'Workflow Test', 'type': 'test', 'price': '750',
            'sample_type': 'Blood', 'test_category': 'General',
            'unit': 'mg/dL', 'reference_ranges': '10-20',
        })
        self.assertEqual(service_response.status_code, 302)
        self.assertTrue(Service.objects.filter(name='Workflow Test').exists())

    def test_inpatient_clinical_workspace_records_round_medicine_and_test(self):
        workspace_url = reverse('inpatient_patient_workspace', args=[self.admission.id])
        page = self.client.get(workspace_url)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Admitted Patients Management')
        self.assertContains(page, self.patient.name)

        round_response = self.client.post(
            reverse('add_inpatient_round', args=[self.admission.id]),
            {
                'doctor_id': str(self.doctor.id), 'round_date': '2026-07-16',
                'round_time': '10:30', 'blood_pressure': '120/80',
                'temperature': '98.6', 'pulse': '72', 'spo2': '98%',
                'clinical_observation': 'Patient is clinically stable.',
                'assessment': 'Improving', 'care_plan': 'Continue monitoring.',
            },
        )
        self.assertEqual(round_response.status_code, 302)
        self.assertTrue(InpatientRound.objects.filter(admission=self.admission).exists())

        medicine_response = self.client.post(
            reverse('add_inpatient_medication', args=[self.admission.id]),
            {
                'medicine_name': 'Paracetamol', 'dose': '500 mg',
                'route': 'Oral', 'frequency': 'Twice daily',
                'duration': '3 days', 'start_date': '2026-07-16',
                'instructions': 'After food',
            },
        )
        self.assertEqual(medicine_response.status_code, 302)
        self.assertTrue(InpatientMedication.objects.filter(admission=self.admission).exists())

        inpatient_service = Service.objects.create(
            name='Inpatient CBC', type='test', price=500, sample_type='Blood',
            test_category='Hematology', unit='g/dL', reference_ranges='Normal',
        )
        test_response = self.client.post(
            reverse('add_inpatient_test', args=[self.admission.id]),
            {'service_id': str(inpatient_service.id), 'priority': 'Urgent', 'clinical_note': 'Monitor infection.'},
        )
        self.assertEqual(test_response.status_code, 302)
        self.assertTrue(InpatientTestOrder.objects.filter(admission=self.admission, priority='Urgent').exists())

    def test_catalog_database_defaults_support_legacy_inserts(self):
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO doctors (
                    name, phone, email, specialization, designation, department,
                    license_number, availability, experience, room_number, consultation_fee
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING is_active
                ''',
                (
                    'Database Default Doctor', '01500000000', 'default@example.com',
                    'Medicine', 'Consultant', 'Medicine', 'DEFAULT-1', 'Daily',
                    3, '103', 400,
                ),
            )
            self.assertEqual(cursor.fetchone()[0], 1)

            cursor.execute(
                '''
                INSERT INTO services (name, type, price)
                VALUES (%s, %s, %s)
                RETURNING is_active
                ''',
                ('Database Default Service', 'doctor', 400),
            )
            self.assertEqual(cursor.fetchone()[0], 1)
