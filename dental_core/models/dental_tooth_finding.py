from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

TOOTH_NAMES = {
    # Upper Right
    '18': ('Upper Right 3rd Molar (Wisdom)', '1', '8\u2518'),
    '17': ('Upper Right 2nd Molar', '2', '7\u2518'),
    '16': ('Upper Right 1st Molar', '3', '6\u2518'),
    '15': ('Upper Right 2nd Premolar', '4', '5\u2518'),
    '14': ('Upper Right 1st Premolar', '5', '4\u2518'),
    '13': ('Upper Right Canine', '6', '3\u2518'),
    '12': ('Upper Right Lateral Incisor', '7', '2\u2518'),
    '11': ('Upper Right Central Incisor', '8', '1\u2518'),
    # Upper Left
    '21': ('Upper Left Central Incisor', '9', '\u25141'),
    '22': ('Upper Left Lateral Incisor', '10', '\u25142'),
    '23': ('Upper Left Canine', '11', '\u25143'),
    '24': ('Upper Left 1st Premolar', '12', '\u25144'),
    '25': ('Upper Left 2nd Premolar', '13', '\u25145'),
    '26': ('Upper Left 1st Molar', '14', '\u25146'),
    '27': ('Upper Left 2nd Molar', '15', '\u25147'),
    '28': ('Upper Left 3rd Molar (Wisdom)', '16', '\u25148'),
    # Lower Left
    '38': ('Lower Left 3rd Molar (Wisdom)', '17', '\u250c8'),
    '37': ('Lower Left 2nd Molar', '18', '\u250c7'),
    '36': ('Lower Left 1st Molar', '19', '\u250c6'),
    '35': ('Lower Left 2nd Premolar', '20', '\u250c5'),
    '34': ('Lower Left 1st Premolar', '21', '\u250c4'),
    '33': ('Lower Left Canine', '22', '\u250c3'),
    '32': ('Lower Left Lateral Incisor', '23', '\u250c2'),
    '31': ('Lower Left Central Incisor', '24', '\u250c1'),
    # Lower Right
    '41': ('Lower Right Central Incisor', '25', '1\u2510'),
    '42': ('Lower Right Lateral Incisor', '26', '2\u2510'),
    '43': ('Lower Right Canine', '27', '3\u2510'),
    '44': ('Lower Right 1st Premolar', '28', '4\u2510'),
    '45': ('Lower Right 2nd Premolar', '29', '5\u2510'),
    '46': ('Lower Right 1st Molar', '30', '6\u2510'),
    '47': ('Lower Right 2nd Molar', '31', '7\u2510'),
    '48': ('Lower Right 3rd Molar (Wisdom)', '32', '8\u2510'),
    # Deciduous Upper Right
    '55': ('Primary Upper Right 2nd Molar', 'A', 'E\u2518'),
    '54': ('Primary Upper Right 1st Molar', 'B', 'D\u2518'),
    '53': ('Primary Upper Right Canine', 'C', 'C\u2518'),
    '52': ('Primary Upper Right Lateral Incisor', 'D', 'B\u2518'),
    '51': ('Primary Upper Right Central Incisor', 'E', 'A\u2518'),
    # Deciduous Upper Left
    '61': ('Primary Upper Left Central Incisor', 'F', '\u2514A'),
    '62': ('Primary Upper Left Lateral Incisor', 'G', '\u2514B'),
    '63': ('Primary Upper Left Canine', 'H', '\u2514C'),
    '64': ('Primary Upper Left 1st Molar', 'I', '\u2514D'),
    '65': ('Primary Upper Left 2nd Molar', 'J', '\u2514E'),
    # Deciduous Lower Left
    '75': ('Primary Lower Left 2nd Molar', 'K', '\u250cE'),
    '74': ('Primary Lower Left 1st Molar', 'L', '\u250cD'),
    '73': ('Primary Lower Left Canine', 'M', '\u250cC'),
    '72': ('Primary Lower Left Lateral Incisor', 'N', '\u250cB'),
    '71': ('Primary Lower Left Central Incisor', 'O', '\u250cA'),
    # Deciduous Lower Right
    '81': ('Primary Lower Right Central Incisor', 'P', 'A\u2510'),
    '82': ('Primary Lower Right Lateral Incisor', 'Q', 'B\u2510'),
    '83': ('Primary Lower Right Canine', 'R', 'C\u2510'),
    '84': ('Primary Lower Right 1st Molar', 'S', 'D\u2510'),
    '85': ('Primary Lower Right 2nd Molar', 'T', 'E\u2510'),
}


class DentalToothFinding(models.Model):
    _name = 'dental.tooth.finding'
    _description = 'Dental Tooth Finding'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'finding_date desc, id desc'

    name = fields.Char(string='Finding Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    patient_id = fields.Many2one('res.partner', string='Patient', required=True, domain=[('is_dental_patient', '=', True)], index=True, tracking=True)
    case_id = fields.Many2one('dental.case', string='Dental Case', index=True, ondelete='cascade', tracking=True)
    examination_id = fields.Many2one('dental.clinical.examination', string='Clinical Examination', index=True)
    doctor_id = fields.Many2one('hr.employee.public', string='Dentist / Doctor', tracking=True)

    tooth_number = fields.Char(string='Tooth Number (FDI)', required=True, index=True, tracking=True)
    universal_number = fields.Char(string='Universal Notation', compute='_compute_notations', store=True)
    palmer_notation = fields.Char(string='Palmer Notation', compute='_compute_notations', store=True)
    tooth_name = fields.Char(string='Tooth Anatomy Name', compute='_compute_notations', store=True)

    condition = fields.Selection([
        ('sound', 'Sound / Healthy'),
        ('caries', 'Caries / Cavity'),
        ('restoration', 'Restoration / Filling'),
        ('missing', 'Missing'),
        ('crown', 'Crown / Cap'),
        ('root_canal', 'Root Canal Treated'),
        ('implant', 'Implant'),
        ('fracture', 'Fracture / Chipped'),
        ('impacted', 'Impacted'),
        ('extraction_indicated', 'Extraction Indicated'),
        ('bridge', 'Bridge Pontic / Abutment'),
        ('other', 'Other Finding')
    ], string='Condition', default='sound', required=True, tracking=True)

    surfaces = fields.Char(string='Affected Surfaces', help='E.g. MOD, B, O, L, D, M, I')
    severity = fields.Selection([
        ('mild', 'Mild / Incipient'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe / Extensive')
    ], string='Severity', default='moderate', tracking=True)

    finding_date = fields.Datetime(string='Recorded Date', default=fields.Datetime.now, required=True, tracking=True)
    diagnosis_id = fields.Many2one('dental.diagnosis', string='Clinical Diagnosis', tracking=True)
    treatment_indicated = fields.Char(string='Proposed Treatment')
    treatment_id = fields.Many2one('product.template', string='Treatment Service', domain=[('is_dental_treatment', '=', True)])
    notes = fields.Text(string='Clinical Notes')

    state = fields.Selection([
        ('active', 'Active Finding'),
        ('planned', 'Treatment Planned'),
        ('completed', 'Treated / Resolved'),
        ('historical', 'Historical')
    ], string='Status', default='active', tracking=True)

    active = fields.Boolean(default=True)

    @api.depends('tooth_number')
    def _compute_notations(self):
        for rec in self:
            info = TOOTH_NAMES.get(str(rec.tooth_number).strip())
            if info:
                rec.tooth_name = info[0]
                rec.universal_number = info[1]
                rec.palmer_notation = info[2]
            else:
                rec.tooth_name = _('Tooth %s') % (rec.tooth_number or '')
                rec.universal_number = rec.tooth_number or ''
                rec.palmer_notation = rec.tooth_number or ''

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dental.tooth.finding') or _('New')
        return super().create(vals_list)
