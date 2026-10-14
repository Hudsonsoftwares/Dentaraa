# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from datetime import date, timedelta

class TestDentalPharmacyDispensing(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.patient = cls.env['res.partner'].create({
            'name': 'Dispense Patient Test',
            'is_dental_patient': True,
        })

        cls.dentist = cls.env['hr.employee'].create({
            'name': 'Dr. Robert Dentist',
            'dental_role': 'dentist',
            'registration_number': 'DR-8888',
        })

        cls.medicine = cls.env['product.product'].create({
            'name': 'Ibuprofen 400mg Test',
            'is_medicine': True,
            'is_storable': True,
            'dosage_form': 'tablet',
            'strength': '400 mg',
            'list_price': 10.0,
            'standard_price': 6.0,
            'reorder_level': 10.0,
            'tracking': 'lot',
        })

        cls.stock_loc = cls.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('company_id', 'in', (cls.env.company.id, False))
        ], limit=1)

        cls.customer_loc = cls.env['stock.location'].search([
            ('usage', '=', 'customer')
        ], limit=1)

        # Create a valid lot
        cls.valid_lot = cls.env['stock.lot'].create({
            'name': 'LOT-VALID-2026',
            'product_id': cls.medicine.id,
            'expiry_date': date.today() + timedelta(days=180),
        })

        # Create an expired lot
        cls.expired_lot = cls.env['stock.lot'].create({
            'name': 'LOT-EXPIRED-2025',
            'product_id': cls.medicine.id,
            'expiry_date': date.today() - timedelta(days=30),
        })

        # Add initial physical stock for the valid lot
        cls.env['stock.quant']._update_available_quantity(
            cls.medicine,
            cls.stock_loc,
            50.0,
            lot_id=cls.valid_lot
        )

    def test_dispensing_workflow(self):
        """Test partial dispensing, over-dispensing prevention, and complete dispensing."""
        # 1. Create prescription for 20 tablets
        rx = self.env['dental.prescription'].create({
            'patient_id': self.patient.id,
            'dentist_id': self.dentist.id,
            'prescription_date': date.today(),
            'line_ids': [(0, 0, {
                'medicine_id': self.medicine.id,
                'quantity': 20.0,
                'dose': '1 tab',
                'route': 'oral',
                'frequency': 'bid',
                'duration': 10,
            })]
        })
        rx.action_confirm()
        self.assertEqual(rx.state, 'confirmed')

        rx_line = rx.line_ids[0]

        # 2. Attempt dispensing with expired batch -> must raise ValidationError
        disp_expired = self.env['dental.pharmacy.dispense'].create({
            'prescription_id': rx.id,
            'location_id': self.stock_loc.id,
            'location_dest_id': self.customer_loc.id,
            'line_ids': [(0, 0, {
                'prescription_line_id': rx_line.id,
                'lot_id': self.expired_lot.id,
                'qty_to_dispense': 10.0,
                'unit_price': 10.0,
            })]
        })
        with self.assertRaises(ValidationError):
            disp_expired.action_dispense()

        # 3. Partial Dispensing: dispense 10 out of 20 with valid lot
        disp_1 = self.env['dental.pharmacy.dispense'].create({
            'prescription_id': rx.id,
            'location_id': self.stock_loc.id,
            'location_dest_id': self.customer_loc.id,
            'line_ids': [(0, 0, {
                'prescription_line_id': rx_line.id,
                'lot_id': self.valid_lot.id,
                'qty_to_dispense': 10.0,
                'unit_price': 10.0,
            })]
        })
        disp_1.action_dispense()
        self.assertEqual(disp_1.state, 'dispensed')
        self.assertEqual(rx_line.dispensed_qty, 10.0)
        self.assertEqual(rx_line.remaining_qty, 10.0)
        self.assertEqual(rx.state, 'partially_dispensed')

        # 4. Attempt to over-dispense: dispense 15 when only 10 remain -> must raise ValidationError
        disp_over = self.env['dental.pharmacy.dispense'].create({
            'prescription_id': rx.id,
            'location_id': self.stock_loc.id,
            'location_dest_id': self.customer_loc.id,
            'line_ids': [(0, 0, {
                'prescription_line_id': rx_line.id,
                'lot_id': self.valid_lot.id,
                'qty_to_dispense': 15.0,
                'unit_price': 10.0,
            })]
        })
        with self.assertRaises(ValidationError):
            disp_over.action_dispense()

        # 5. Complete remaining dispensing: dispense remaining 10
        disp_2 = self.env['dental.pharmacy.dispense'].create({
            'prescription_id': rx.id,
            'location_id': self.stock_loc.id,
            'location_dest_id': self.customer_loc.id,
            'line_ids': [(0, 0, {
                'prescription_line_id': rx_line.id,
                'lot_id': self.valid_lot.id,
                'qty_to_dispense': 10.0,
                'unit_price': 10.0,
            })]
        })
        disp_2.action_dispense()
        self.assertEqual(disp_2.state, 'dispensed')
        self.assertEqual(rx_line.dispensed_qty, 20.0)
        self.assertEqual(rx_line.remaining_qty, 0.0)
        self.assertEqual(rx.state, 'fully_dispensed')
