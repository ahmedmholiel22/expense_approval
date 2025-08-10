from odoo import models, fields, api
from odoo.exceptions import ValidationError


class RegisterPaymentWizard(models.TransientModel):
    _name = 'register.payment.wizard'
    _description = 'Register Payment Wizard'

    request_id = fields.Many2one('expense.approval.request', string="Expense Request", required=True)
    partner_id = fields.Many2one('res.partner', string="Partner")
    amount = fields.Float(string="Amount", required=True)
    journal_id = fields.Many2one('account.journal', string="Journal", required=True, domain="[('type', 'in', ('bank', 'cash'))]")
    payment_date = fields.Date(string="Payment Date", default=fields.Date.context_today)
    payment_method_id = fields.Many2one(
        'account.payment.method'
    )

    def action_register_payment(self):
        self.ensure_one()

        payment = self.env['account.payment'].create({
            'expense_request_id': self.request_id.id,
            'payment_method_id': self.payment_method_id.id,
            'partner_id': self.partner_id.id,
            'amount': self.amount,
            'payment_date': self.payment_date,
            'journal_id': self.journal_id.id,
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'expense_request_ref': self.request_id.name,
        })

        payment.post()
        self.request_id.actual_transfer_date = self.payment_date
