# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date, datetime

class DentalPharmacyDashboard(models.AbstractModel):
    _name = 'dental.pharmacy.dashboard'
    _description = 'Dental Pharmacy Live Analytics Dashboard'

    @api.model
    def get_dashboard_data(self):
        """Fetches live real database metrics for the Pharmacy OWL Dashboard."""
        today = fields.Date.context_today(self)
        now = fields.Datetime.now()
        start_of_today = datetime.combine(today, datetime.min.time())
        end_of_today = datetime.combine(today, datetime.max.time())

        Product = self.env['product.product']
        Lot = self.env['stock.lot']
        Prescription = self.env['dental.prescription']
        Dispense = self.env['dental.pharmacy.dispense']

        # 1. Medicine Catalog Inventory Counts
        medicines = Product.search([('is_medicine', '=', True)])
        total_medicines = len(medicines)
        out_of_stock = len(medicines.filtered(lambda m: m.qty_available <= 0))
        low_stock = len(medicines.filtered(lambda m: 0 < m.qty_available <= m.reorder_level))
        in_stock = len(medicines.filtered(lambda m: m.qty_available > m.reorder_level))

        # 2. Batch / Lot Expiry Counts
        lots = Lot.search([('is_medicine', '=', True)])
        total_batches = len(lots)
        expired_batches = len(lots.filtered(lambda l: l.expiry_status == 'expired'))
        near_expiry_batches = len(lots.filtered(lambda l: l.expiry_status == 'near_expiry'))
        valid_batches = len(lots.filtered(lambda l: l.expiry_status == 'valid'))

        # 3. Prescription Lifecycle Counts
        all_rx = Prescription.search([])
        total_prescriptions = len(all_rx)
        pending_prescriptions = Prescription.search_count([('state', '=', 'confirmed')])
        partially_dispensed = Prescription.search_count([('state', '=', 'partially_dispensed')])
        fully_dispensed = Prescription.search_count([('state', '=', 'fully_dispensed')])
        draft_prescriptions = Prescription.search_count([('state', '=', 'draft')])

        # 4. Dispensing Financial & Operational Metrics
        today_dispenses = Dispense.search([
            ('dispense_date', '>=', start_of_today),
            ('dispense_date', '<=', end_of_today),
            ('state', '=', 'dispensed')
        ])
        today_dispensed_count = len(today_dispenses)
        today_dispensed_amount = sum(today_dispenses.mapped('amount_total'))

        all_dispensed = Dispense.search([('state', '=', 'dispensed')])
        total_dispensed_amount = sum(all_dispensed.mapped('amount_total'))

        # 5. Tables & Queues (Real Data)
        # Recent Dispenses
        recent_dispenses_records = Dispense.search([], order='dispense_date desc, id desc', limit=6)
        recent_dispenses = [{
            'id': d.id,
            'name': d.name,
            'patient_name': d.patient_id.name or 'N/A',
            'dentist_name': d.dentist_id.name or 'N/A',
            'date': fields.Datetime.to_string(d.dispense_date),
            'amount_total': d.amount_total,
            'state': d.state,
            'has_invoice': bool(d.invoice_id),
            'invoice_id': d.invoice_id.id if d.invoice_id else False,
            'invoice_state': d.invoice_state or 'None',
        } for d in recent_dispenses_records]

        # Pending Prescriptions
        pending_rx_records = Prescription.search([
            ('state', 'in', ('confirmed', 'partially_dispensed'))
        ], order='prescription_date desc, id desc', limit=6)
        pending_prescriptions_list = [{
            'id': rx.id,
            'name': rx.name,
            'patient_name': rx.patient_id.name or 'N/A',
            'dentist_name': rx.dentist_id.name or 'N/A',
            'date': fields.Date.to_string(rx.prescription_date),
            'remaining_qty': rx.total_remaining_qty,
            'prescribed_qty': rx.total_prescribed_qty,
            'state': rx.state,
        } for rx in pending_rx_records]

        # Low Stock Items
        low_stock_records = medicines.filtered(lambda m: m.qty_available <= m.reorder_level)
        low_stock_list = [{
            'id': m.id,
            'name': m.name,
            'generic_name': m.generic_name or '',
            'qty_available': m.qty_available,
            'reorder_level': m.reorder_level,
            'dosage_unit': m.dosage_unit or 'Units',
            'status': 'Out of Stock' if m.qty_available <= 0 else 'Low Stock'
        } for m in low_stock_records[:6]]

        # Near Expiry / Expired Batches
        critical_lots = lots.filtered(lambda l: l.expiry_status in ('expired', 'near_expiry'))
        critical_lots_sorted = sorted(critical_lots, key=lambda l: (l.expiry_date or date(2099, 12, 31)))
        near_expiry_list = [{
            'id': l.id,
            'name': l.name,
            'product_name': l.product_id.name or '',
            'expiry_date': fields.Date.to_string(l.expiry_date) if l.expiry_date else 'No Date',
            'days_to_expiry': l.days_to_expiry,
            'status': 'Expired' if l.expiry_status == 'expired' else 'Near Expiry',
            'available_qty': l.available_qty,
        } for l in critical_lots_sorted[:6]]

        return {
            'total_medicines': total_medicines,
            'in_stock': in_stock,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock,
            'total_batches': total_batches,
            'valid_batches': valid_batches,
            'near_expiry_batches': near_expiry_batches,
            'expired_batches': expired_batches,
            'total_prescriptions': total_prescriptions,
            'pending_prescriptions': pending_prescriptions,
            'partially_dispensed': partially_dispensed,
            'fully_dispensed': fully_dispensed,
            'draft_prescriptions': draft_prescriptions,
            'today_dispensed_count': today_dispensed_count,
            'today_dispensed_amount': today_dispensed_amount,
            'total_dispensed_amount': total_dispensed_amount,
            'currency_symbol': self.env.company.currency_id.symbol or '$',
            'recent_dispenses': recent_dispenses,
            'pending_prescriptions_list': pending_prescriptions_list,
            'low_stock_list': low_stock_list,
            'near_expiry_list': near_expiry_list,
        }
