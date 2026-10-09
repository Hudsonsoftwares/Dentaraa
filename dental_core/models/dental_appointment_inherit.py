from odoo import models, fields, api, _

class DentalAppointment(models.Model):
    _inherit = 'dental.appointment'

    case_ids = fields.One2many('dental.case', 'appointment_id', string='Clinical Cases')
    case_count = fields.Integer(string='Case Count', compute='_compute_case_count')

    @api.depends('case_ids')
    def _compute_case_count(self):
        for appt in self:
            appt.case_count = len(appt.case_ids)

    def action_open_clinical_case(self):
        self.ensure_one()
        if self.case_ids:
            # Open existing case
            case = self.case_ids[0]
            action = self.env['ir.actions.act_window']._for_xml_id('dental_core.action_dental_case')
            action['res_id'] = case.id
            action['views'] = [(self.env.ref('dental_core.view_dental_case_form').id, 'form')]
            return action
        else:
            # Create a new case
            case_vals = {
                'patient_id': self.patient_id.id,
                'doctor_id': self.doctor_id.id,
                'appointment_id': self.id,
                'branch_id': self.branch_id.id,
            }
            case = self.env['dental.case'].create(case_vals)
            action = self.env['ir.actions.act_window']._for_xml_id('dental_core.action_dental_case')
            action['res_id'] = case.id
            action['views'] = [(self.env.ref('dental_core.view_dental_case_form').id, 'form')]
            return action

    def action_start_consultation(self):
        super(DentalAppointment, self).action_start_consultation()
        return self.action_open_clinical_case()
