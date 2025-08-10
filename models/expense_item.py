from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ExpenseApprovalMainItem(models.Model):
    _name = 'expense.approval.main.item'
    _description = 'Main Expense Item'

    name = fields.Char(string="Main Expense Name", required=True)
    sub_item_ids = fields.One2many(
        'expense.approval.sub.item',
        'main_item_id',
        string='Sub Items'
    )
    approval_level_ids = fields.One2many(
        'expense.approval.level',
        'main_item_id',
        string="Approval Levels",
        copy=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Vendor'
    )
    acc_number = fields.Char('Account Number')
    has_product = fields.Boolean()

    @api.constrains('acc_number')
    def _check_iban_sa(self):
        for rec in self:
            if rec.acc_number:
                acc = rec.acc_number.replace(' ', '').upper()
                if not acc.startswith('SA'):
                    raise ValidationError("Account number must start with 'SA'.")
                if len(acc) != 24:
                    raise ValidationError("Saudi IBAN must be exactly 24 characters (e.g., SA + 22 digits).")
                if not acc[2:].isdigit():
                    raise ValidationError("IBAN after 'SA' must contain only digits.")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'approval_level_ids' in fields_list:
            res['approval_level_ids'] = [(0, 0, {
                'sequence': 1, 'level_name': 'مدير القسم', 
            }), (0, 0, {
                'sequence': 2, 'level_name': 'مدير الإدارة', 
            }), (0, 0, {
                'sequence': 3, 'level_name': 'مشرف الحسابات', 
            }), (0, 0, {
                'sequence': 4, 'level_name': 'رئيس الحسابات', 
            }), (0, 0, {
                'sequence': 5, 'level_name': 'نائب الرئيس', 
            }), (0, 0, {
                'sequence': 6, 'level_name': 'الرئيس التنفيذي', 
            })]
        return res


class ExpenseApprovalSubItem(models.Model):
    _name = 'expense.approval.sub.item'
    _description = 'Sub Expense Item'

    name = fields.Char(string='Name', required=True)
    main_item_id = fields.Many2one(
        'expense.approval.main.item',
        string='Main Expense Item',
        required=True, ondelete='cascade'
    )
    has_product = fields.Boolean()
