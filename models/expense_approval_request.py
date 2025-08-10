from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ExpenseApprovalRequest(models.Model):
    _name = 'expense.approval.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Expense Approval Request'

    name = fields.Char(
        string="Reference",
        required=True, default='New',
        tracking=True
    )
    date = fields.Date(string="Request Date", default=fields.Date.context_today)
    department_id = fields.Many2one(
        'expense.approval.department',
        string="Department", required=True, tracking=True
    )
    main_item_id = fields.Many2one(
        'expense.approval.main.item',
        string="Main Expense Item", required=True,
        tracking=True
    )
    sub_item_id = fields.Many2one(
        'expense.approval.sub.item',
        string="Sub Expense Item",
        tracking=True
    )
    amount = fields.Float(
        string="Amount",
        compute="_compute_amount_all",
        store=True,
    )
    description = fields.Text(
        string="Notes",
        tracking=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='draft',
        string="Status",
        tracking=True
    )

    budget_line_id = fields.Many2one(
        'expense.approval.budget',
        string="Budget Line",
        compute="_compute_budget_line",
        store=True,
    )
    approval_line_ids = fields.One2many(
        'expense.approval.line',
        'request_id',
        string="Approval Steps"
    )
    can_approve = fields.Boolean(
        string="Can Approve",
        compute="_compute_can_approve"
    )
    can_approve_store = fields.Boolean()
    expected_transfer_date = fields.Date(
    tracking=True
    )
    actual_transfer_date = fields.Date(
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Vendor',
        tracking=True
    )
    acc_number = fields.Char(
        'Account Number',
        tracking=True
    )
    planned_amount = fields.Float(
        string="Budget Amount",
        compute='_compute_budget_amounts',
        store=True,
        tracking=True
    )
    used_amount = fields.Float(
        string="Used Amount",
        compute='_compute_budget_amounts',
        store=True,
        tracking=True
    )
    remaining_amount = fields.Float(
        string="Remaining Amount",
        compute='_compute_budget_amounts',
        store=True,
        tracking=True
    )
    product_line_ids = fields.One2many(
        'expense.product.line',
        'request_id',
        string="Product Lines"
    )
    payment_count = fields.Integer(
        compute='_compute_payment_count'
    )
    bill_count = fields.Integer(
        compute='_compute_bill_count'
    )
    journal_entry_count = fields.Integer(
        compute='_compute_journal_entry_count'
    )
    attachments_ids = fields.Many2many(
        'ir.attachment',
        string="Attachments"
    )
    currency_id = fields.Many2one(
        'res.currency',
        readonly=True, default=lambda self: self.env.company.currency_id
    )
    amount_untaxed = fields.Monetary(
        string="Untaxed Amount",
        compute="_compute_amount_all",
        store=True,
        currency_field='currency_id'
    )
    amount_tax = fields.Monetary(
        string='Taxes', store=True,
        readonly=True,
        compute='_compute_amount_all'
    )
    paid_amount = fields.Monetary(
        string='Paid Amount', store=True,
        readonly=True,
        compute='_compute_amount_all'
    )
    amount_total = fields.Monetary(
        string="Total Amount",
        compute="_compute_amount_all",
        store=True,
        currency_field='currency_id'
    )
    remaining_amount_total = fields.Monetary(
        string="Remaining Amount",
        compute="_compute_amount_all",
        store=True,
        currency_field='currency_id'
    )
    has_product = fields.Boolean(
        compute='compute_has_product'
    )
    has_approved_before = fields.Boolean(
        compute='_compute_has_approved_before'
    )
    has_approved_before_stored = fields.Boolean()
    is_over_budget = fields.Boolean(
        compute='compute_is_over_budget',
        store=True
    )
    is_in_budget = fields.Boolean(
        compute='compute_is_in_budget',
        store=True
    )
    over_budget_comment = fields.Text()

    @api.depends('amount','remaining_amount','budget_line_id')
    def compute_is_over_budget(self):
        for rec in self:
            if rec.budget_line_id and rec.amount > 0 and rec.amount > rec.remaining_amount:
                rec.is_over_budget = True
            else:
                rec.is_over_budget = False

    @api.depends('amount','remaining_amount','budget_line_id')
    def compute_is_in_budget(self):
        for rec in self:
            if rec.budget_line_id and rec.amount > 0 and rec.amount < rec.remaining_amount:
                rec.is_in_budget = True
            else:
                rec.is_in_budget = False

    def _compute_has_approved_before(self):
        current_user = self.env.user
        for rec in self:
            rec.has_approved_before = any(
                line.user_id == current_user and line.state == 'approved'
                for line in rec.approval_line_ids
            )
            rec.has_approved_before_stored = rec.has_approved_before

    def compute_has_product(self):
        for rec in self:
            if rec.main_item_id and rec.main_item_id.has_product:
                rec.has_product = True
            elif rec.sub_item_id and rec.sub_item_id.has_product:
                rec.has_product = True
            else:
                rec.has_product = False
                
    @api.depends('product_line_ids.subtotal')
    def _compute_amount_all(self):
        for rec in self:
            payments = self.env['account.payment'].search([
                ('expense_request_id', '=', rec.id),
                ('state', '=', 'posted')
            ])
            rec.amount_untaxed = sum(rec.product_line_ids.mapped('subtotal'))
            rec.amount_tax = sum(rec.product_line_ids.mapped('tax_amount'))
            rec.paid_amount = sum(payments.mapped('amount'))
            rec.amount_total = (rec.amount_untaxed + rec.amount_tax)
            rec.amount = rec.amount_total
            rec.remaining_amount_total = rec.amount_total - rec.paid_amount

    def _compute_journal_entry_count(self):
        for rec in self:
            rec.journal_entry_count = self.env['account.move'].search_count([('type', '=', 'entry'),('expense_request_id', '=', self.id)])


    def _compute_bill_count(self):
        for rec in self:
            rec.bill_count = self.env['account.move'].search_count([('type', '=', 'in_invoice'),('expense_request_id', '=', self.id)])


    def _compute_payment_count(self):
        for rec in self:
            rec.payment_count = self.env['account.payment'].search_count(
                [('expense_request_id', '=', self.id)])

    @api.depends('budget_line_id', 'budget_line_id.planned_amount', 'budget_line_id.used_amount','state','amount')
    def _compute_budget_amounts(self):
        for rec in self:
            if rec.budget_line_id:
                rec.planned_amount = rec.budget_line_id.planned_amount or 0.0
                rec.used_amount = rec.budget_line_id.used_amount or 0.0
                rec.remaining_amount = rec.planned_amount - rec.used_amount
            else:
                rec.planned_amount = 0.0
                rec.used_amount = 0.0
                rec.remaining_amount = 0.0


    @api.onchange('main_item_id')
    def _onchange_main_item_id(self):
        """ main_item_id """
        for rec in self:
            if rec.main_item_id:
                rec.partner_id = rec.main_item_id.partner_id.id
                rec.acc_number = rec.main_item_id.acc_number

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """ partner_id """
        for rec in self:
            if not rec.partner_id:
                rec.acc_number = ""

    @api.constrains('expected_transfer_date')
    def _check_expected_transfer_date(self):
        """ Validate  expected_transfer_date"""
        for rec in self:
            today = fields.Date.today()
            if rec.expected_transfer_date and rec.expected_transfer_date < today:
                raise ValidationError("Expected Transfer Date Must Be In The Future.")

    # @api.depends('approval_line_ids.state', 'approval_line_ids.user_id')
    def _compute_can_approve(self):
        for rec in self:
            current_user = self.env.user

            pending_lines = rec.approval_line_ids.filtered(lambda l: l.state == 'pending').sorted('sequence')
            if pending_lines:
                current_line = pending_lines[0]
                if current_line.user_id == current_user:
                    rec.can_approve = True
                else:
                    rec.can_approve = False
            else:
                rec.can_approve = False

            rec.can_approve_store = rec.can_approve

    @api.depends('expected_transfer_date', 'department_id', 'main_item_id', 'sub_item_id')
    def _compute_budget_line(self):
        for record in self:
            if not (record.expected_transfer_date and record.department_id and record.main_item_id):
                record.budget_line_id = False
                continue

            year = record.expected_transfer_date.year
            month = str(record.expected_transfer_date.month)

            domain = [
                ('department_id', '=', record.department_id.id),
                ('main_item_id', '=', record.main_item_id.id),
                ('year', '=', year),
                ('month', '=', month),
            ]

            if record.sub_item_id:
                domain.append(('sub_item_id', '=', record.sub_item_id.id))

            budget_line = self.env['expense.approval.budget'].search(domain, limit=1)
            record.budget_line_id = budget_line.id if budget_line else False

    @api.constrains('amount', 'budget_line_id', 'state')
    def _check_budget_limit(self):
        for record in self:
            if record.state == 'approved' and record.budget_line_id:
                remaining = record.budget_line_id.planned_amount - record.budget_line_id.used_amount
                if record.amount > remaining:
                    raise ValidationError(_("Requested amount exceeds remaining budget."))

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('expense.approval.request') or 'New'
        return super().create(vals)

    def _assign_next_approver_activity(self):
        for request in self:
            next_line = request.approval_line_ids.filtered(
                lambda l: l.state == 'pending')[:1]

            if next_line:
                request.activity_schedule(
                    'mail.activity_data_todo',  # نوع الإشعار
                    user_id=next_line.user_id.id,
                    note="يرجى مراجعة طلب التعميد والموافقة عليه.",
                )

    def create_approval_activity(self, user_id):
        """Create a To-Do activity for the given approver."""
        activity_type = self.env.ref('mail.activity_data_todo', raise_if_not_found=False) or \
                        self.env['mail.activity.type'].search([('name', '=', 'To Do')], limit=1)

        if activity_type:
            for rec in self:
                note = ''
                if rec.is_over_budget:
                    note = rec.over_budget_comment
                else:
                    note = 'يرجى مراجعة الطلب واتخاذ القرار.'

                self.env['mail.activity'].create({
                    'res_model_id': self.env['ir.model']._get_id('expense.approval.request'),
                    'res_id': rec.id,
                    'activity_type_id': activity_type.id,
                    'summary': 'مطلوب الموافقة على طلب التعميد',
                    'user_id': user_id.id,
                    'note': note,
                })

    def generate_approval_lines(self):
        for rec in self:
            rec.approval_line_ids.unlink()
            main_item = rec.main_item_id
            levels = main_item.approval_level_ids.filtered(lambda l: l.is_approved)
            if levels:
                lines = []
                for level in levels.sorted(key=lambda l: l.sequence):
                    lines.append((0, 0, {
                        'user_id': level.user_id.id,
                        'sequence': level.sequence,
                        'level_name': level.level_name,
                        'state': 'pending'
                    }))
                rec.approval_line_ids = lines
            else:
                raise ValidationError(_("please enter approval level for expense"))

    @api.onchange('amount')
    def _onchange_amount_warning(self):
        for rec in self:
            if rec.amount and rec.remaining_amount and rec.amount > rec.remaining_amount:
                return {
                    'warning': {
                        'title': "Warning",
                        'message': "This request is over budget",
                    }
                }
    # @api.constrains('amount')
    # def _check_amount_not_exceed_remaining(self):
    #     for rec in self:
    #         if rec.amount and rec.remaining_amount and rec.amount > rec.remaining_amount:
    #             raise ValidationError("This request is over budget")

    def remove_activity(self, user_id):
        """Remove pending approval activities for the given user."""
        for rec in self:
            self.env['mail.activity'].search([
                ('res_model', '=', 'expense.approval.request'),
                ('res_id', '=', rec.id),
                ('user_id', '=', user_id.id),
                ('activity_type_id.name', '=', 'To Do')
            ]).unlink()

    def send_approval_email(self, user, record_name):
        if not user or not user.email:
            return
        body = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.5;">
            <p>مرحباً <strong>{user.name}</strong>,</p>
            <p>لديك طلب تعميد بحاجة إلى موافقتك.</p>
            <ul>
                <li><strong>رقم التعميد:</strong> {record_name}</li>
            </ul>
            <p>يرجى الدخول إلى النظام والموافقة أو الرفض حسب ما تراه مناسبًا.</p>
            <p>تحياتي،<br/><strong>نظام الموافقات</strong></p>
        </div>
        """
        mail_values = {
            'subject': f'طلب موافقة جديد: {record_name}',
            'body_html': body,
            'email_to': user.email,
        }
        self.env['mail.mail'].create(mail_values).send()

    def action_submit(self):
        for rec in self:
            rec.generate_approval_lines()
            if rec.amount > rec.remaining_amount:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': 'Over Budget',
                        'res_model': 'over.budget.wizard',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'target': 'new',
                        'context': {
                            'default_request_id': self.id,
                        },
                    }
            else:
                first_line = self.approval_line_ids[0]
                if first_line.user_id:
                    self.create_approval_activity(first_line.user_id)
                    # self.send_approval_email(first_line.user_id, rec.name)
                rec.state = 'in_progress'

    def action_set_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_approve(self):
        for rec in self:
            current_user = self.env.user

            pending_lines = rec.approval_line_ids.filtered(
                lambda l: l.state == 'pending').sorted('sequence')
            if not pending_lines:
                continue

            current_line = pending_lines[0]
            if current_line.user_id != current_user:
                raise ValidationError("لا يمكنك الموافقة قبل دورك.")

            current_line.state = 'approved'
            current_line.approval_date = fields.Datetime.now()
            rec.message_post(body=f"تمت الموافقة من قبل {current_user.name}")
            rec.remove_activity(current_line.user_id)

            next_line = rec.approval_line_ids.filtered(
                lambda l: l.state == 'pending').sorted('sequence')
            if next_line:
                rec.create_approval_activity(next_line[0].user_id)
                # rec.send_approval_email(next_line[0].user_id, rec.name)
            else:
                rec.state = 'approved'

    def action_reject(self):
        self.ensure_one()
        current_user = self.env.user

        pending_lines = self.approval_line_ids.filtered(
            lambda l: l.state == 'pending').sorted('sequence')
        if not pending_lines:
            raise ValidationError("لا يوجد من يمكنه الرفض حالياً.")

        current_line = pending_lines[0]

        if current_line.user_id != current_user:
            raise ValidationError("ليس لديك صلاحية الرفض في هذه المرحلة.")

        current_line.write({'state': 'rejected'})

        self.state = 'rejected'

        self.remove_activity(current_line.user_id)

        self.message_post(body=f"تم رفض طلب التعميد من {current_user.name}")

    @api.onchange('sub_item_id','main_item_id')
    def _onchange_sub_item_id(self):
        for rec in self:
            if rec.sub_item_id:
                rec.main_item_id = rec.sub_item_id.main_item_id.id
            sub_items = self.env['expense.approval.sub.item'].search([])
            if rec.main_item_id:
                return {
                    'domain': {'sub_item_id': [('main_item_id', '=', rec.main_item_id.id)]},
                }
            else:
                return {
                    'domain': {'sub_item_id': [('id', 'in', sub_items.ids)]},
                }
    # models/expense_approval_request.py

    def action_open_register_payment_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Register Payment',
            'res_model': 'register.payment.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {
                'default_request_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_amount': self.amount,
            },
        }

    def action_view_payment(self):
        rec_ids = self.env['account.payment'].search([
            ('expense_request_id', '=', self.id)])
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customer Payments'),
            'res_model': 'account.payment',
            'view_type': 'list,form',
            'view_mode': 'list,form',
            'target': 'current',
            'context': {
                'edit': False,
                'create': False,
                'delete': False,
                'duplicate': False,
            },
            'domain': [('id', 'in', rec_ids.ids)],
        }

    def action_view_bill(self):
        rec_ids = self.env['account.move'].search([('type', '=', 'in_invoice'),('expense_request_id', '=', self.id)])
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bills'),
            'res_model': 'account.move',
            'view_type': 'list,form',
            'view_mode': 'list,form',
            'target': 'current',
            'context': {
                'edit': False,
                'create': False,
                'delete': False,
                'duplicate': False,
            },
            'domain': [('id', 'in', rec_ids.ids)],
        }

    def action_view_journal_entry(self):
        rec_ids = self.env['account.move'].search([('type', '=', 'entry'),('expense_request_id', '=', self.id)])
        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal Entry'),
            'res_model': 'account.move',
            'view_type': 'list,form',
            'view_mode': 'list,form',
            'target': 'current',
            'context': {
                'edit': False,
                'create': False,
                'delete': False,
                'duplicate': False,
            },
            'domain': [('id', 'in', rec_ids.ids)],
        }

    def action_create_bill(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Bill'),
            'res_model': 'account.move',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_type': 'in_invoice',
                'default_partner_id': self.partner_id.id,
                'default_expense_request_ref': f"Expense Request #{self.name}",
                'default_expense_request_id': self.id,
            },
        }

    def action_journal_entry(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Journal Entry'),
            'res_model': 'account.move',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_type': 'entry',
                'default_partner_id': self.partner_id.id,
                'default_expense_request_ref': f"Expense Request #{self.name}",
                'default_expense_request_id': self.id,
            },
        }


class ExpenseApprovalLine(models.Model):
    _name = 'expense.approval.line'
    _description = 'Expense Approval Line'


    request_id = fields.Many2one('expense.approval.request', string="Request", ondelete='cascade')
    sequence = fields.Integer(string="Sequence")
    level_name = fields.Char(string="Level")
    user_id = fields.Many2one('res.users', string="Approver")
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending', string="Status")
    approval_date = fields.Datetime(string="Approval Date")
    comment = fields.Text(string="Comment")


class ExpenseProductLine(models.Model):
    _name = 'expense.product.line'
    _description = 'Expense Product Line'

    request_id = fields.Many2one('expense.approval.request', string="Request")
    product_id = fields.Many2one('product.product', string="Product")
    description = fields.Char(string="Description")
    quantity = fields.Float(string="Quantity", default=1.0)
    unit_price = fields.Float(string="Unit Price")

    discount_amount = fields.Float(string="Discount Amount")
    discount_percent = fields.Float(string="Discount (%)")

    tax_id = fields.Many2one('account.tax', string="Tax")
    tax_amount = fields.Float(string="Tax Amount", compute="_compute_subtotal", store=True)

    subtotal = fields.Float(string="Subtotal", compute="_compute_subtotal", store=True)

    @api.depends('quantity', 'unit_price', 'discount_amount', 'discount_percent', 'tax_id')
    def _compute_subtotal(self):
        for line in self:
            price = line.unit_price * line.quantity

            if line.discount_amount:
                price -= line.discount_amount
            elif line.discount_percent:
                price *= (1 - line.discount_percent / 100.0)

            price = max(price, 0.0)

            tax = 0.0
            if line.tax_id and line.tax_id.amount_type == 'percent':
                tax = price * (line.tax_id.amount / 100.0)

            line.tax_amount = tax
            line.subtotal = price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.description = line.product_id.name
                line.unit_price = line.product_id.lst_price

    @api.onchange('discount_amount')
    def _onchange_discount_amount(self):
        if self.discount_amount:
            self.discount_percent = 0.0

    @api.onchange('discount_percent')
    def _onchange_discount_percent(self):
        if self.discount_percent:
            self.discount_amount = 0.0


