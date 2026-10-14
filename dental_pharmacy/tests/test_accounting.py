# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from datetime import date, timedelta

class TestDentalPharmacyAccounting(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.patient = cls.env['res.partner'].create({
            'name': 'Billing Patient Test',
            'is_dental_patient': True,
        })

        cls.dentist = cls.env['hr.employee'].create({
            'name': 'Dr. Billing Test',
            'dental_role': 'dentist',
        })

        cls.medicine = cls.env['product.product'].create({
            'name': 'Chlorhexidine 0.2% Billing Test',
            'is_medicine': True,
            'is_storable': True,
            'list_price': 50.0,
            'tracking': 'lot',
        })

        cls.stock_loc = cls.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('company_id', 'in', (cls.env.company.id, False))
        ], limit=1)

        cls.customer_loc = cls.env['stock.location'].search([
            ('usage', '=', 'customer')
        ], limit=1)

        cls.lot = cls.env['stock.lot'].create({
            'name': 'BATCH-BILL-01',
            'product_id': cls.medicine.id,
            'expiry_date': date.today() + timedelta(days=90),
        })

        cls.env['stock.quant']._update_available_quantity(
            cls.medicine,
            cls.stock_loc,
            20.0,
            lot_id=cls.lot
        )

        cls.income_account = cls.env['account.account'].search([
            ('account_type', '=', 'income')
        ], limit=1)
        if not cls.income_account:
            cls.income_account = cls.env['account.account'].create({
                'name': 'Pharmacy Sales Income Test',
                'code': '400000',
                'account_type': 'income',
            })

        cls.recv_account = cls.env['account.account'].search([
            ('account_type', '=', 'asset_receivable')
        ], limit=1)
        if not cls.recv_account:
            cls.recv_account = cls.env['account.account'].create({
                'name': 'Accounts Receivable Test',
                'code': '120000',
                'account_type': 'asset_receivable',
            })
        cls.patient.property_account_receivable_id = cls.recv_account

        cls.sale_journal = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', 'in', (cls.env.company.id, False))
        ], limit=1)
        if not cls.sale_journal:
            cls.sale_journal = cls.env['account.journal'].create({
                'name': 'Customer Invoices Test',
                'code': 'SINV',
                'type': 'sale',
                'company_id': cls.env.company.id,
            })

    def test_customer_invoice_generation(self):
        """Test generating customer invoice, checking separation from dispensing, and duplicate protection."""
        rx = self.env['dental.prescription'].create({
            'patient_id': self.patient.id,
            'dentist_id': self.dentist.id,
            'prescription_date': date.today(),
            'line_ids': [(0, 0, {
                'medicine_id': self.medicine.id,
                'quantity': 2.0,
                'dose': '15 ml',
                'route': 'topical',
                'frequency': 'bid',
                'duration': 7,
            })]
        })
        rx.action_confirm()

        disp = self.env['dental.pharmacy.dispense'].create({
            'prescription_id': rx.id,
            'location_id': self.stock_loc.id,
            'location_dest_id': self.customer_loc.id,
            'line_ids': [(0, 0, {
                'prescription_line_id': rx.line_ids[0].id,
                'lot_id': self.lot.id,
                'qty_to_dispense': 2.0,
                'unit_price': 50.0,
            })]
        })
        disp.action_dispense()
        self.assertEqual(disp.state, 'dispensed')
        self.assertFalse(disp.invoice_id)

        # Generate Invoice
        disp.action_create_invoice()
        self.assertTrue(disp.invoice_id)
        invoice = disp.invoice_id

        # Verification: Invoice is Draft and Unpaid (strict separation maintained)
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(invoice.partner_id, self.patient)
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(invoice.dental_prescription_id, rx)
        self.assertEqual(invoice.pharmacy_dispense_id, disp)
        self.assertTrue(invoice.is_pharmacy_invoice)

        # Prevent duplicate invoices
        with self.assertRaises(UserError):
            disp.action_create_invoice()
