# -*- coding: utf-8 -*-
# Copyright 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    contract_id = fields.Many2one(
        'contract',
        string='Contract')
    date_start = fields.Date(
        string='Date Start',
        help="Start date of the invoiced period")
    date_end = fields.Date(
        string='Date End',
        help="End date of the invoiced period")
