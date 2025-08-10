from odoo import models, fields, api
from odoo.exceptions import ValidationError


class OverBudgetWizard(models.TransientModel):
    _name = 'over.budget.wizard'
    _description = 'Over Budget Wizard'

    request_id = fields.Many2one('expense.approval.request', string="Expense Request", required=True)
    comment = fields.Text()

    def action_send(self):
        self.request_id.over_budget_comment = self.comment

        self.request_id.generate_approval_lines()
        first_line = self.request_id.approval_line_ids[0]
        if first_line.user_id:
            self.request_id.create_approval_activity(first_line.user_id)
        self.request_id.state = 'in_progress'