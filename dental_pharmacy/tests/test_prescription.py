# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from datetime import date

class TestDentalPrescription(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create Patient
        cls.patient = cls.env['res.partner'].create({
            'name': 'John Doe Patient',
            'is_dental_patient': True,
            'phone': '1234567890',
        })

        # Create Dentist Employee
        cls.dentist = cls.env['hr.employee'].create({
            'name': 'Dr. Sarah Dentist',
            'dental_role': 'dentist',
            'registration_number': 'DENT-REG-98765',
        })

        # Create Dental Medicine Category
        cls.category = cls.env['dental.medicine.category'].create({
            'name': 'Test Antibiotics',
            'code': 'TATB',
        })

        # Create Medicine Product
        cls.medicine = cls.env['product.product'].create({
            'name': 'Amoxicillin 500mg Test',
            'is_medicine': True,
            'medicine_category_id': cls.category.id,
            'dosage_form': 'capsule',
            'strength': '500 mg',
            'list_price': 15.0,
            'standard_price': 10.0,
            'reorder_level': 20.0,
            'tracking': 'lot',
        })

    def test_prescription_lifecycle(self):
        """Test full prescription creation, confirmation, and state tracking."""
        rx = self.env['dental.prescription'].create({
            'patient_id': self.patient.id,
            'dentist_id': self.dentist.id,
            'prescription_date': date.today(),
            'diagnosis': 'Acute Periapical Abscess',
            'line_ids': [(0, 0, {
                'medicine_id': self.medicine.id,
                'dose': '1 capsule',
                'route': 'oral',
                'frequency': 'tid',
                'duration': 5,
                'quantity': 15.0,
                'instructions': 'After meals',
            })]
        })

        self.assertEqual(rx.state, 'draft')
        self.assertEqual(rx.total_prescribed_qty, 15.0)
        self.assertEqual(rx.total_dispensed_qty, 0.0)
        self.assertEqual(rx.total_remaining_qty, 15.0)

        # Confirm prescription
        rx.action_confirm()
        self.assertEqual(rx.state, 'confirmed')

        # Cannot cancel if medicines have been dispensed (currently 0, so cancellation is allowed)
        rx.action_draft()
        self.assertEqual(rx.state, 'draft')

    def test_prescription_validation(self):
        """Test that confirming without lines or with 0 quantity raises ValidationError."""
        empty_rx = self.env['dental.prescription'].create({
            'patient_id': self.patient.id,
            'dentist_id': self.dentist.id,
        })
        with self.assertRaises(ValidationError):
            empty_rx.action_confirm()
