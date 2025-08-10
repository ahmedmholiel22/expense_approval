from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    expense_request_id = fields.Many2one('expense.approval.request', string="Expense Request")
    expense_request_ref = fields.Char(string="Expense Request Reference")
