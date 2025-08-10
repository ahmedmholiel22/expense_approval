from odoo import models, fields

class ExpenseApprovalDepartment(models.Model):
    _name = 'expense.approval.department'
    _description = 'Expense Approval Department'

    name = fields.Char(string="Department Name", required=True)
