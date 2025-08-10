
{
    'name': 'Expense Approvals',
    'summary': 'Manage expense approval setup and budget planning',
    'author': "Ahmed Holiel",
    'company': 'Elghomlas',
    'version': '13.0.0.1.0',
    'category': '',
    'license': 'AGPL-3',
    'sequence': 1,
    'depends': [
        'base',
        'mail',
        'product',
        'account',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        # 'report/',
        'wizard/register_payment_wizard_view.xml',
        'views/department_view.xml',
        'views/expense_item_view.xml',
        'views/approval_budget.xml',
        'views/account_payment.xml',
        'views/account_move.xml',
        'views/expense_approval_request.xml',

        'data/expense_approval_request_seq.xml',
    ],
    'demo': [
        # 'demo/',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

