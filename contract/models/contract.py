# -*- coding: utf-8 -*-
# Copyright 2004-2010 OpenERP SA
# Copyright 2014 Angel Moya <angel.moya@domatix.com>
# Copyright 2015 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2016-2017 Carlos Dauden <carlos.dauden@tecnativa.com>
# Copyright 2016-2017 LasLabs Inc.
# Copyright 2018 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class Contract(models.Model):
    _name = 'contract'
    _description = 'Contract'                                          
    _inherit = ['mail.thread', 'active.date']

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id)
    name = fields.Char(
        string='Contract',
        index=True,
        required=True,
        track_visibility='onchange')
    code = fields.Char(
        string='Reference',
        index=True,
        track_visibility='onchange')
    recurring_rule_type = fields.Selection(
        [('daily', 'Day(s)'),
         ('weekly', 'Week(s)'),
         ('monthly', 'Month(s)'),
         ('monthlylastday', 'Month(s) last day'),
         ('yearly', 'Year(s)')],
        default='monthly',
        string='Recurrence',
        help="Specify Interval for automatic invoice generation.")
    recurring_invoicing_type = fields.Selection(
        [('pre-paid', 'Pre-paid'),
         ('post-paid', 'Post-paid')],
        default='pre-paid',
        string='Invoicing type',
        help="Specify if process date is 'from' or 'to' invoicing date")
    recurring_interval = fields.Integer(
        default=1,
        string='Repeat Every',
        help="Repeat every (Days/Week/Month/Year)")
    template = fields.Boolean(
        string='Contract is a template',
        help="A contract template can not have parter or active_date_start"
             "filled.\n"
             "If contract is not a template those fields are required.")
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        auto_join=True,
        track_visibility='onchange')
    date_start = fields.Date(
        string='Date Start',
        default=fields.Date.context_today)
    date_end = fields.Date(
        string='Date End',
        index=True)
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic account',
        track_visibility='onchange')
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist')
    contract_template_id = fields.Many2one(
        string='Contract Template',
        readonly=True,
        comodel_name='contract')
    contract_line_ids = fields.One2many(
        string='Contract Lines',
        comodel_name='contract.line',
        inverse_name='contract_id',
        copy=True)
    automatic_invoices = fields.Boolean(
        string='Generate invoices automatically')
    next_invoice_date = fields.Date(
        default=fields.Date.context_today,
        copy=False,
        string='Date of Next Invoice')
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Responsible',
        index=True,
        default=lambda self: self.env.user)
    create_invoice_visibility = fields.Boolean(
        compute='_compute_create_invoice_visibility')

    @api.depends('next_invoice_date', 'date_end')
    def _compute_create_invoice_visibility(self):
        for contract in self:
            contract.create_invoice_visibility = (
                not contract.date_end or
                contract.next_invoice_date <= contract.date_end)

    @api.onchange('date_start')
    def _onchange_date_start(self):
        if self.date_start:
            self.next_invoice_date = self.date_start

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.pricelist_id = self.partner_id.property_product_pricelist.id

    @api.constrains('partner_id', 'template')
    def _check_partner_id_contracts(self):
        for contract in self.filtered(lambda c: not c.template):
            if not contract.partner_id:
                raise ValidationError(
                    _("You must supply a customer for the contract '%s'") %
                    contract.name)

    @api.constrains('next_invoice_date', 'date_start')
    def _check_next_invoice_date_start_date(self):
        for contract in self.filtered('next_invoice_date'):
            if contract.date_start > contract.next_invoice_date:
                raise ValidationError(
                    _("You can't have a next invoicing date before the start "
                      "of the contract '%s'") % contract.name)

    @api.constrains('next_invoice_date', 'template')
    def _check_next_invoice_date_contracts(self):
        for contract in self.filtered(lambda c: not c.template):
            if not contract.next_invoice_date:
                raise ValidationError(
                    _("You must supply a next invoicing date for contract "
                      "'%s'") % contract.name)

    @api.constrains('date_start', 'template')
    def _check_date_start_contracts(self):
        for contract in self.filtered(lambda c: not c.template):
            if not contract.date_start:
                raise ValidationError(
                    _("You must supply a start date for contract '%s'") %
                    contract.name)

    @api.constrains('date_start', 'date_end')
    def _check_start_end_dates(self):
        for contract in self.filtered('date_end'):
            if contract.date_start > contract.date_end:
                raise ValidationError(
                    _("Contract '%s' start date can't be later than end date")
                    % contract.name)

    @api.model
    def get_relative_delta(self, recurring_rule_type, interval):
        if recurring_rule_type == 'daily':
            return relativedelta(days=interval)
        elif recurring_rule_type == 'weekly':
            return relativedelta(weeks=interval)
        elif recurring_rule_type == 'monthly':
            return relativedelta(months=interval)
        elif recurring_rule_type == 'monthlylastday':
            return relativedelta(months=interval, day=31)
        else:
            return relativedelta(years=interval)

    @api.model
    def _insert_markers(self, line, date_start, next_date, date_format):
        contract = line.analytic_account_id
        if contract.recurring_invoicing_type == 'pre-paid':
            date_from = date_start
            date_to = next_date - relativedelta(days=1)
        else:
            date_from = (
                date_start -
                self.get_relative_delta(
                    contract.recurring_rule_type,
                    contract.recurring_interval) +
                relativedelta(days=1))
            date_to = date_start
        name = line.name
        name = name.replace('#START#', date_from.strftime(date_format))
        name = name.replace('#END#', date_to.strftime(date_format))
        return name

    @api.model
    def _prepare_invoice_line(self, line, invoice_id):
        invoice_line = self.env['account.invoice.line'].new({
            'invoice_id': invoice_id,
            'product_id': line.product_id.id,
            'quantity': line.quantity,
            'uom_id': line.uom_id.id,
            'discount': line.discount})
        # Get other invoice line values from product onchange
        invoice_line._onchange_product_id()
        invoice_line_vals = invoice_line._convert_to_write(invoice_line._cache)
        # Insert markers
        name = line.name
        contract = line.analytic_account_id
        if 'old_date' in self.env.context and 'next_date' in self.env.context:
            lang_obj = self.env['res.lang']
            lang = lang_obj.search(
                [('code', '=', contract.partner_id.lang)])
            date_format = lang.date_format or '%m/%d/%Y'
            name = self._insert_markers(
                line, self.env.context['old_date'],
                self.env.context['next_date'], date_format)
        invoice_line_vals.update({
            'name': name,
            'account_analytic_id': contract.id,
            'price_unit': line.price_unit})
        return invoice_line_vals

    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        if not self.partner_id:
            raise ValidationError(
                _("You must first select a Customer for Contract %s!") %
                self.name)
        journal = self.analytic_account_id.journal_id or \
            self.env['account.journal'].search([
                ('type', '=', 'sale'),
                ('company_id', '=', self.company_id.id)],
                limit=1)
        if not journal:
            raise ValidationError(
                _("Please define a sale journal for the company '%s'.") %
                (self.company_id.name or '',))
        currency = (
            self.pricelist_id.currency_id or
            self.partner_id.property_product_pricelist.currency_id or
            self.company_id.currency_id)
        invoice = self.env['account.invoice'].new({
            'reference': self.code,
            'type': 'out_invoice',
            'partner_id': self.partner_id.address_get(
                ['invoice'])['invoice'],
            'currency_id': currency.id,
            'journal_id': journal.id,
            'date_invoice': self.next_invoice_date,
            'origin': self.name,
            'company_id': self.company_id.id,
            'contract_id': self.id,
            'user_id': self.partner_id.user_id.id})
        # Get other invoice values from partner onchange
        invoice._onchange_partner_id()
        return invoice._convert_to_write(invoice._cache)

    @api.multi
    def _create_invoice(self):
        self.ensure_one()
        invoice_vals = self._prepare_invoice()
        invoice = self.env['account.invoice'].create(invoice_vals)
        for line in self.contract_line_ids:
            invoice_line_vals = self._prepare_invoice_line(line, invoice.id)
            self.env['account.invoice.line'].create(invoice_line_vals)
        invoice.compute_taxes()
        return invoice

    @api.multi
    def recurring_create_invoice(self):
        """Create invoices from contracts

        :return: invoices created
        """
        invoices = self.env['account.invoice']
        for contract in self:
            ref_date = contract.next_invoice_date or fields.Date.today()
            if (contract.date_start > ref_date or
                    contract.date_end and contract.date_end < ref_date):
                if self.env.context.get('cron'):
                    continue  # Don't fail on cron jobs
                raise ValidationError(
                    _("You must review start and end dates!\n%s") %
                    contract.name)
            old_date = fields.Date.from_string(ref_date)
            new_date = old_date + self.get_relative_delta(
                contract.recurring_rule_type, contract.recurring_interval)
            ctx = self.env.context.copy()
            ctx.update({
                'old_date': old_date,
                'next_date': new_date,
                # Force company for correct evaluation of domain access rules
                'force_company': contract.company_id.id})
            # Re-read contract with correct company
            invoices |= contract.with_context(ctx)._create_invoice()
            contract.write({
                'next_invoice_date': fields.Date.to_string(new_date)})
        return invoices

    @api.model
    def cron_recurring_create_invoice(self):
        today = fields.Date.today()
        contracts = self.with_context(cron=True).search([
            ('template', '=', False),
            ('next_invoice_date', '<=', today),
            '|',
            ('date_end', '=', False),
            ('date_end', '>=', today)])
        return contracts.recurring_create_invoice()

    @api.multi
    def action_contract_send(self):
        self.ensure_one()
        template = self.env.ref('contract.email_contract_template', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form')
        ctx = dict(
            default_model='account.analytic.account',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment')
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx}
