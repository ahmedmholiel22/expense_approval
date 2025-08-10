from odoo import models, fields


class ExpenseApprovalLevel(models.Model):
    _name = 'expense.approval.level'
    _description = 'Approval Level'

    main_item_id = fields.Many2one('expense.approval.main.item', string="Main Expense Item", required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string="Approver User")
    level_name = fields.Char(string="Level Name", readonly=1)
    sequence = fields.Integer(string="Sequence", default=1, readonly=1)
    is_approved = fields.Boolean(default=False)
