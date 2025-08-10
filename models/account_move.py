from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    expense_request_id = fields.Many2one('expense.approval.request', string="Expense Request")
    expense_request_ref = fields.Char(string="Expense Request Reference")

