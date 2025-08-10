from odoo import models, fields, api
from datetime import datetime

def _get_year_selection():
    current_year = datetime.today().year
    return [(str(y), str(y)) for y in range(current_year - 5, current_year + 26)]

class ExpenseApprovalBudget(models.Model):
    _name = 'expense.approval.budget'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Monthly Budget'

    name = fields.Char(
        string="Reference",
        readonly=True, copy=False,
        default='New',
        tracking=True
    )
    main_item_id = fields.Many2one(
        'expense.approval.main.item',
        string="Main Expense", required=True,
        tracking=True
    )
    sub_item_id = fields.Many2one(
        'expense.approval.sub.item',
        string="Sub Expense", required=True,
        tracking=True
    )
    department_id = fields.Many2one(
        'expense.approval.department',
        string="Department", required=True,
        tracking=True
    )
    year = fields.Selection(
        selection=_get_year_selection(),
        string="Year",
        required=True,
        tracking=True,
        default=lambda self: str(datetime.today().year),
    )
    month = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string="Month", required=True,
        tracking=True
    )
    planned_amount = fields.Float(
        string="Budget Amount",
        tracking=True
    )
    used_amount = fields.Float(
        string="Used Amount",
        compute='_compute_used_amount'
    )
    used_amount_cash_flow = fields.Float(
        string="Used Amount",
        compute='_compute_used_amount_cash_flow'
    )
    used_amount_store = fields.Float()
    used_amount_cash_flow_store = fields.Float()
    remaining_amount = fields.Float(
        string="Remaining Amount",
        compute='_compute_remaining_amount'
    )
    various_amount = fields.Float(
        string="Various Amount",
        compute='_compute_various_amount'
    )
    remaining_amount_store = fields.Float()
    various_amount_store = fields.Float()

    
    def _compute_various_amount(self):
        for rec in self:
            rec.various_amount = rec.planned_amount - rec.used_amount_cash_flow
            rec.various_amount_store = rec.various_amount
    
    def _compute_used_amount_cash_flow(self):
        for record in self:
            domain = [
                ('department_id', '=', record.department_id.id),
                ('main_item_id', '=', record.main_item_id.id),
                ('sub_item_id', '=', record.sub_item_id.id),
                ('state', 'not in', ['draft','rejected']),
            ]
            if record.year and record.month:
                domain += [
                    ('actual_transfer_date', '>=', f'{record.year}-{int(record.month):02d}-01'),
                    ('actual_transfer_date', '<', f'{record.year}-{int(record.month)+1:02d}-01') if int(record.month) < 12
                    else ('actual_transfer_date', '<', f'{record.year + 1}-01-01')
                ]
            approvals = self.env['expense.approval.request'].search(domain)
            record.used_amount_cash_flow = sum(approvals.mapped('amount'))
            record.used_amount_cash_flow_store = record.used_amount_cash_flow
            
    def _compute_remaining_amount(self):
        for rec in self:
            rec.remaining_amount = rec.planned_amount - rec.used_amount
            rec.remaining_amount_store = rec.remaining_amount

    def _compute_used_amount(self):
        for record in self:
            domain = [
                ('department_id', '=', record.department_id.id),
                ('main_item_id', '=', record.main_item_id.id),
                ('sub_item_id', '=', record.sub_item_id.id),
                ('state', 'not in', ['draft','rejected']),
            ]
            if record.year and record.month:
                domain += [
                    ('expected_transfer_date', '>=', f'{record.year}-{int(record.month):02d}-01'),
                    ('expected_transfer_date', '<', f'{record.year}-{int(record.month)+1:02d}-01') if int(record.month) < 12
                    else ('expected_transfer_date', '<', f'{record.year + 1}-01-01')
                ]
            approvals = self.env['expense.approval.request'].search(domain)
            record.used_amount = sum(approvals.mapped('amount'))
            record.used_amount_store = record.used_amount

    @api.onchange('sub_item_id')
    def _onchange_sub_item_id(self):
        """ sub_item_id """
        for rec in self:
            if rec.sub_item_id:
                rec.main_item_id = rec.sub_item_id.main_item_id.id

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('expense.approval.budget') or 'New'
        return super().create(vals)