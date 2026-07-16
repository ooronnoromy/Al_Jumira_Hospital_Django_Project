from django.db import models


class Admin(models.Model):
    username = models.TextField(unique=True)
    password = models.TextField()
    email = models.TextField(unique=True, blank=True, null=True)
    class Meta: db_table = 'admins'


class Patient(models.Model):
    daily_patient_id = models.IntegerField(blank=True, null=True)
    name = models.TextField()
    age = models.IntegerField()
    gender = models.TextField()
    phone = models.TextField()
    email = models.TextField(blank=True, null=True)
    dob = models.TextField()
    blood_group = models.TextField()
    address = models.TextField()
    emergency_contact_name = models.TextField(blank=True, null=True)
    emergency_contact_phone = models.TextField(blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True)
    created_at = models.TextField(blank=True, null=True)
    age_unit = models.TextField(default='Y', blank=True, null=True)
    serial_no = models.TextField(blank=True, null=True)
    patient_status = models.TextField(blank=True, null=True)
    doctor_name = models.TextField(blank=True, null=True)
    doctor_designation = models.TextField(blank=True, null=True)
    referer_name = models.TextField(blank=True, null=True)
    doctor_fee = models.FloatField(default=0, blank=True, null=True)
    doctor_paid_amount = models.FloatField(default=0, blank=True, null=True)
    doctor_due_amount = models.FloatField(default=0, blank=True, null=True)
    source_patient_id = models.IntegerField(blank=True, null=True)
    served_by = models.TextField(default='Admin')
    class Meta: db_table = 'patients'


class User(models.Model):
    username = models.TextField(unique=True)
    password = models.TextField()
    email = models.TextField(unique=True, blank=True, null=True)
    class Meta: db_table = 'users'


class UserPermission(models.Model):
    user = models.ForeignKey(User, models.CASCADE, db_column='user_id')
    page_key = models.TextField()
    class Meta:
        db_table = 'user_permissions'
        constraints = [models.UniqueConstraint(fields=['user', 'page_key'], name='uniq_user_page_key')]


class AppMigration(models.Model):
    migration_key = models.TextField(primary_key=True)
    applied_at = models.TextField()
    class Meta: db_table = 'app_migrations'


class Doctor(models.Model):
    name = models.TextField()
    phone = models.TextField()
    email = models.TextField()
    specialization = models.TextField()
    designation = models.TextField(blank=True, null=True)
    department = models.TextField()
    license_number = models.TextField()
    availability = models.TextField()
    experience = models.IntegerField()
    room_number = models.TextField()
    consultation_fee = models.FloatField(default=0, db_default=0)
    is_active = models.IntegerField(default=1, db_default=1)
    class Meta: db_table = 'doctors'


class Service(models.Model):
    name = models.TextField()
    type = models.TextField()
    price = models.FloatField()
    sample_type = models.TextField(blank=True, null=True)
    test_category = models.TextField(blank=True, null=True)
    unit = models.TextField(blank=True, null=True)
    reference_ranges = models.TextField(blank=True, null=True)
    is_active = models.IntegerField(default=1, db_default=1)
    class Meta: db_table = 'services'


class DoctorFeeDueCollection(models.Model):
    patient = models.ForeignKey(Patient, models.DO_NOTHING, db_column='patient_id')
    previous_due = models.FloatField()
    collection_amount = models.FloatField(default=0)
    discount_amount = models.FloatField(default=0)
    remaining_due = models.FloatField(default=0)
    payment_method = models.TextField(default='Cash')
    note = models.TextField(blank=True, null=True)
    collected_by = models.TextField(blank=True, null=True)
    created_at = models.TextField()
    class Meta: db_table = 'doctor_fee_due_collections'


class PatientVisitReturn(models.Model):
    return_no = models.TextField(unique=True)
    patient = models.OneToOneField(Patient, models.DO_NOTHING, db_column='patient_id')
    patient_uhid = models.IntegerField(blank=True, null=True)
    ticket_no = models.IntegerField(blank=True, null=True)
    patient_name = models.TextField()
    phone = models.TextField(blank=True, null=True)
    doctor_name = models.TextField(blank=True, null=True)
    doctor_fee = models.FloatField(default=0)
    refund_amount = models.FloatField(default=0)
    reason = models.TextField(blank=True, null=True)
    return_date = models.TextField()
    created_by = models.TextField(blank=True, null=True)
    created_at = models.TextField()
    class Meta: db_table = 'patient_visit_returns'


class TestOrder(models.Model):
    patient = models.ForeignKey(Patient, models.DO_NOTHING, db_column='patient_id', blank=True, null=True)
    service = models.ForeignKey(Service, models.DO_NOTHING, db_column='service_id', blank=True, null=True)
    test_date = models.TextField(blank=True, null=True)
    class Meta: db_table = 'test_orders'


class DoctorPrescription(models.Model):
    prescription_no = models.TextField(unique=True)
    prescription_date = models.TextField()
    patient = models.ForeignKey(Patient, models.DO_NOTHING, db_column='patient_id')
    doctor = models.ForeignKey(Doctor, models.DO_NOTHING, db_column='doctor_id')
    vitals_json = models.TextField(blank=True, null=True)
    clinical_json = models.TextField(blank=True, null=True)
    medicines_json = models.TextField(blank=True, null=True)
    created_by = models.TextField(blank=True, null=True)
    created_at = models.TextField()
    class Meta: db_table = 'doctor_prescriptions'


class DoctorPrescriptionDraft(models.Model):
    patient = models.OneToOneField(Patient, models.DO_NOTHING, db_column='patient_id')
    doctor = models.ForeignKey(Doctor, models.DO_NOTHING, db_column='doctor_id', blank=True, null=True)
    draft_json = models.TextField()
    updated_by = models.TextField(blank=True, null=True)
    updated_at = models.TextField()
    class Meta: db_table = 'doctor_prescription_drafts'


class TestBill(models.Model):
    invoice_no = models.TextField(unique=True)
    patient = models.ForeignKey(Patient, models.DO_NOTHING, db_column='patient_id')
    doctor_name = models.TextField(blank=True, null=True)
    referred_by = models.TextField(blank=True, null=True)
    sample_status = models.TextField(blank=True, null=True)
    delivery_time = models.TextField(blank=True, null=True)
    subtotal = models.FloatField(default=0)
    discount_amount = models.FloatField(default=0)
    total_amount = models.FloatField(default=0)
    received_amount = models.FloatField(default=0)
    due_amount = models.FloatField(default=0)
    change_amount = models.FloatField(default=0)
    payment_method = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_by = models.TextField(blank=True, null=True)
    created_at = models.TextField()
    class Meta: db_table = 'test_bills'


class TestBillItem(models.Model):
    test_bill = models.ForeignKey(TestBill, models.CASCADE, db_column='test_bill_id')
    service = models.ForeignKey(Service, models.DO_NOTHING, db_column='service_id', blank=True, null=True)
    test_name = models.TextField()
    price = models.FloatField(default=0)
    result_value = models.TextField(blank=True, null=True)
    result_note = models.TextField(blank=True, null=True)
    result_updated_at = models.TextField(blank=True, null=True)
    result_updated_by = models.TextField(blank=True, null=True)
    class Meta: db_table = 'test_bill_items'


class TestBillReturn(models.Model):
    return_no = models.TextField(unique=True)
    test_bill = models.OneToOneField(TestBill, models.DO_NOTHING, db_column='test_bill_id')
    invoice_no = models.TextField()
    patient_id = models.IntegerField()
    patient_uhid = models.IntegerField(blank=True, null=True)
    ticket_no = models.IntegerField(blank=True, null=True)
    patient_name = models.TextField()
    phone = models.TextField(blank=True, null=True)
    original_subtotal = models.FloatField(default=0)
    original_discount_amount = models.FloatField(default=0)
    original_total_amount = models.FloatField(default=0)
    original_received_amount = models.FloatField(default=0)
    original_due_amount = models.FloatField(default=0)
    refund_amount = models.FloatField(default=0)
    reason = models.TextField(blank=True, null=True)
    return_date = models.TextField()
    created_by = models.TextField(blank=True, null=True)
    created_at = models.TextField()
    class Meta: db_table = 'test_bill_returns'


class Bill(models.Model):
    patient = models.ForeignKey(Patient, models.DO_NOTHING, db_column='patient_id', blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    total_amount = models.FloatField(default=0, blank=True, null=True)
    created_at = models.TextField(blank=True, null=True)
    class Meta: db_table = 'bills'


class BillItem(models.Model):
    bill = models.ForeignKey(Bill, models.DO_NOTHING, db_column='bill_id', blank=True, null=True)
    service = models.ForeignKey(Service, models.DO_NOTHING, db_column='service_id', blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    price = models.FloatField(blank=True, null=True)
    class Meta: db_table = 'bill_items'


class Admission(models.Model):
    patient = models.ForeignKey(Patient, models.DO_NOTHING, db_column='patient_id')
    doctor = models.ForeignKey(Doctor, models.DO_NOTHING, db_column='doctor_id', blank=True, null=True)
    admission_date = models.TextField()
    ward = models.TextField()
    room_number = models.TextField(blank=True, null=True)
    bed_number = models.TextField()
    admission_fee = models.FloatField(default=0)
    guardian_name = models.TextField(blank=True, null=True)
    guardian_relation = models.TextField(blank=True, null=True)
    reason = models.TextField()
    notes = models.TextField(blank=True, null=True)
    status = models.TextField(default='Admitted')
    discharged_at = models.TextField(blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    admitted_by = models.TextField(default='Admin')
    created_at = models.TextField()
    class Meta: db_table = 'admissions'


class InpatientRound(models.Model):
    admission = models.ForeignKey(Admission, models.CASCADE, db_column='admission_id')
    doctor = models.ForeignKey(Doctor, models.DO_NOTHING, db_column='doctor_id', blank=True, null=True)
    round_date = models.TextField()
    round_time = models.TextField(blank=True, null=True)
    blood_pressure = models.TextField(blank=True, null=True)
    temperature = models.TextField(blank=True, null=True)
    pulse = models.TextField(blank=True, null=True)
    respiratory_rate = models.TextField(blank=True, null=True)
    spo2 = models.TextField(blank=True, null=True)
    clinical_observation = models.TextField()
    assessment = models.TextField(blank=True, null=True)
    care_plan = models.TextField(blank=True, null=True)
    doctor_name = models.TextField(blank=True, null=True)
    created_by = models.TextField(blank=True, null=True)
    created_at = models.TextField()
    class Meta:
        db_table = 'inpatient_rounds'
        ordering = ['-id']


class InpatientMedication(models.Model):
    admission = models.ForeignKey(Admission, models.CASCADE, db_column='admission_id')
    medicine_name = models.TextField()
    dose = models.TextField()
    route = models.TextField(default='Oral')
    frequency = models.TextField()
    duration = models.TextField(blank=True, null=True)
    start_date = models.TextField()
    instructions = models.TextField(blank=True, null=True)
    status = models.TextField(default='Active')
    prescribed_by = models.TextField(blank=True, null=True)
    created_at = models.TextField()
    class Meta:
        db_table = 'inpatient_medications'
        ordering = ['-id']


class InpatientTestOrder(models.Model):
    admission = models.ForeignKey(Admission, models.CASCADE, db_column='admission_id')
    service = models.ForeignKey(Service, models.DO_NOTHING, db_column='service_id', blank=True, null=True)
    test_name = models.TextField()
    priority = models.TextField(default='Routine')
    clinical_note = models.TextField(blank=True, null=True)
    status = models.TextField(default='Ordered')
    ordered_by = models.TextField(blank=True, null=True)
    ordered_at = models.TextField()
    class Meta:
        db_table = 'inpatient_test_orders'
        ordering = ['-id']


class DischargeBill(models.Model):
    admission = models.OneToOneField(Admission, models.DO_NOTHING, db_column='admission_id')
    patient = models.ForeignKey(Patient, models.DO_NOTHING, db_column='patient_id')
    patient_uhid = models.IntegerField(blank=True, null=True)
    bill_no = models.TextField()
    admission_date = models.TextField(blank=True, null=True)
    discharge_date = models.TextField(blank=True, null=True)
    stay_days = models.IntegerField(default=1)
    bed_charge = models.FloatField(default=0)
    doctor_fee = models.FloatField(default=0)
    medicine_charge = models.FloatField(default=0)
    pathology_charge = models.FloatField(default=0)
    service_charge = models.FloatField(default=0)
    other_charge = models.FloatField(default=0)
    total_amount = models.FloatField(default=0)
    discount = models.FloatField(default=0)
    gross_amount = models.FloatField(default=0)
    paid_amount = models.FloatField(default=0)
    due_amount = models.FloatField(default=0)
    change_amount = models.FloatField(default=0)
    remarks = models.TextField(blank=True, null=True)
    prepared_by = models.TextField(blank=True, null=True)
    payment_method = models.TextField(default='Cash')
    created_at = models.TextField()
    updated_at = models.TextField()
    class Meta: db_table = 'discharge_bills'


class DutyRecord(models.Model):
    staff_role = models.TextField()
    doctor = models.ForeignKey(Doctor, models.DO_NOTHING, db_column='doctor_id', blank=True, null=True)
    staff_name = models.TextField()
    duty_date = models.TextField()
    shift = models.TextField()
    ward = models.TextField()
    round_completed = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)
    created_by = models.TextField(blank=True, null=True)
    created_at = models.TextField()
    class Meta: db_table = 'duty_records'


class DailyExpense(models.Model):
    expense_date = models.TextField()
    category = models.TextField()
    description = models.TextField(blank=True, null=True)
    vendor = models.TextField(blank=True, null=True)
    amount = models.FloatField()
    payment_method = models.TextField(default='Cash')
    note = models.TextField(blank=True, null=True)
    created_by = models.TextField(blank=True, null=True)
    created_at = models.TextField()
    class Meta: db_table = 'daily_expenses'


class ExpenseCategory(models.Model):
    name = models.TextField(unique=True)
    created_at = models.TextField()
    class Meta: db_table = 'expense_categories'


class PatientQueueState(models.Model):
    doctor = models.ForeignKey(Doctor, models.DO_NOTHING, db_column='doctor_id')
    queue_date = models.TextField()
    current_patient = models.ForeignKey(Patient, models.DO_NOTHING, db_column='current_patient_id', blank=True, null=True)
    current_ticket_no = models.IntegerField(blank=True, null=True)
    updated_by = models.TextField(blank=True, null=True)
    updated_at = models.TextField()
    class Meta:
        db_table = 'patient_queue_state'
        constraints = [models.UniqueConstraint(fields=['doctor', 'queue_date'], name='uniq_doctor_queue_date')]


class MedicineTransaction(models.Model):
    medicine_name = models.TextField()
    batch_no = models.TextField()
    unit_type = models.TextField(default='strip')
    transaction_type = models.TextField()
    quantity = models.IntegerField()
    price = models.FloatField()
    transaction_date = models.TextField()
    note = models.TextField(blank=True, null=True)
    created_by = models.TextField(blank=True, null=True)
    created_at = models.TextField()
    class Meta: db_table = 'medicine_transactions'


class MedicineSale(models.Model):
    invoice_no = models.TextField(unique=True)
    customer_name = models.TextField()
    customer_phone = models.TextField(blank=True, null=True)
    customer_address = models.TextField(blank=True, null=True)
    subtotal = models.FloatField(default=0)
    discount_type = models.TextField(default='flat')
    discount_value = models.FloatField(default=0)
    discount_amount = models.FloatField(default=0)
    tax_type = models.TextField(default='none')
    tax_value = models.FloatField(default=0)
    tax_amount = models.FloatField(default=0)
    delivery_cost = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    received_amount = models.FloatField(default=0)
    due_amount = models.FloatField(default=0)
    change_amount = models.FloatField(default=0)
    payment_type = models.TextField(default='Cash')
    sale_date = models.TextField()
    created_by = models.TextField(blank=True, null=True)
    created_at = models.TextField()
    class Meta: db_table = 'medicine_sales'


class MedicineSaleItem(models.Model):
    sale = models.ForeignKey(MedicineSale, models.DO_NOTHING, db_column='sale_id')
    medicine_name = models.TextField()
    batch_no = models.TextField()
    unit_type = models.TextField()
    quantity = models.IntegerField()
    unit_price = models.FloatField()
    discount = models.FloatField(default=0)
    line_total = models.FloatField(default=0)
    class Meta: db_table = 'medicine_sale_items'


class MedicineReturn(models.Model):
    return_no = models.TextField(unique=True)
    sale = models.ForeignKey(MedicineSale, models.DO_NOTHING, db_column='sale_id')
    invoice_no = models.TextField()
    customer_name = models.TextField()
    customer_phone = models.TextField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    subtotal = models.FloatField(default=0)
    discount_amount = models.FloatField(default=0)
    refund_amount = models.FloatField(default=0)
    return_date = models.TextField()
    created_by = models.TextField(blank=True, null=True)
    created_at = models.TextField()
    class Meta: db_table = 'medicine_returns'


class MedicineReturnItem(models.Model):
    return_record = models.ForeignKey(MedicineReturn, models.DO_NOTHING, db_column='return_id')
    sale_item = models.ForeignKey(MedicineSaleItem, models.DO_NOTHING, db_column='sale_item_id')
    medicine_name = models.TextField()
    batch_no = models.TextField()
    unit_type = models.TextField()
    quantity = models.IntegerField()
    unit_price = models.FloatField()
    discount = models.FloatField(default=0)
    line_total = models.FloatField(default=0)
    class Meta: db_table = 'medicine_return_items'


class Log(models.Model):
    user_id = models.IntegerField(blank=True, null=True)
    role = models.TextField()
    actor_name = models.TextField(blank=True, null=True)
    patient_id = models.IntegerField(blank=True, null=True)
    action = models.TextField(blank=True, null=True)
    timestamp = models.TextField(blank=True, null=True)
    class Meta: db_table = 'logs'
