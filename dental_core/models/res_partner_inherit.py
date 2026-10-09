from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    dental_case_ids = fields.One2many('dental.case', 'patient_id', string='Dental Cases')
    dental_case_count = fields.Integer(compute='_compute_dental_case_count')
    
    dental_examination_ids = fields.One2many('dental.clinical.examination', 'patient_id', string='Clinical Examinations')
    dental_examination_count = fields.Integer(compute='_compute_dental_examination_count')
    
    dental_diagnosis_ids = fields.One2many('dental.patient.diagnosis', 'patient_id', string='Diagnoses')
    dental_diagnosis_count = fields.Integer(compute='_compute_dental_diagnosis_count')
    
    treatment_plan_ids = fields.One2many('dental.treatment.plan', 'patient_id', string='Treatment Plans')
    treatment_plan_count = fields.Integer(compute='_compute_treatment_plan_count')
    
    treatment_session_ids = fields.One2many('dental.treatment.session', 'patient_id', string='Treatment Sessions')
    treatment_session_count = fields.Integer(compute='_compute_treatment_session_count')

    @api.depends('dental_case_ids')
    def _compute_dental_case_count(self):
        for partner in self:
            partner.dental_case_count = len(partner.dental_case_ids)

    @api.depends('dental_examination_ids')
    def _compute_dental_examination_count(self):
        for partner in self:
            partner.dental_examination_count = len(partner.dental_examination_ids)

    @api.depends('dental_diagnosis_ids')
    def _compute_dental_diagnosis_count(self):
        for partner in self:
            partner.dental_diagnosis_count = len(partner.dental_diagnosis_ids)

    @api.depends('treatment_plan_ids')
    def _compute_treatment_plan_count(self):
        for partner in self:
            partner.treatment_plan_count = len(partner.treatment_plan_ids)

    @api.depends('treatment_session_ids')
    def _compute_treatment_session_count(self):
        for partner in self:
            partner.treatment_session_count = len(partner.treatment_session_ids)

    def action_view_dental_cases(self):
        self.ensure_one()
        return {
            'name': 'Dental Cases',
            'type': 'ir.actions.act_window',
            'res_model': 'dental.case',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    def action_view_dental_examinations(self):
        self.ensure_one()
        return {
            'name': 'Clinical Examinations',
            'type': 'ir.actions.act_window',
            'res_model': 'dental.clinical.examination',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    def action_view_dental_diagnoses(self):
        self.ensure_one()
        return {
            'name': 'Diagnoses',
            'type': 'ir.actions.act_window',
            'res_model': 'dental.patient.diagnosis',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    def action_view_treatment_plans(self):
        self.ensure_one()
        return {
            'name': 'Treatment Plans',
            'type': 'ir.actions.act_window',
            'res_model': 'dental.treatment.plan',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    def action_view_treatment_sessions(self):
        self.ensure_one()
        return {
            'name': 'Treatment Sessions',
            'type': 'ir.actions.act_window',
            'res_model': 'dental.treatment.session',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }
