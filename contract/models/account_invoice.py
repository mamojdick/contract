# -*- coding: utf-8 -*-
# © 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    contract_id = fields.Many2one(
        'account.analytic.account',
        string='Contract')
    
    x_invoiced_period = fields.Char(
        string="Invoiced Period",
        required=False,
    )