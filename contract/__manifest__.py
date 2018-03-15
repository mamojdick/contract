# -*- coding: utf-8 -*-
# Copyright 2004-2010 OpenERP SA
# Copyright 2014-2017 Tecnativa - Pedro M. Baeza
# Copyright 2015 Domatix
# Copyright 2016-2017 Tecnativa - Carlos Dauden
# Copyright 2017 Tecnativa - Vicent Cubells
# Copyright 2016-2017 LasLabs Inc.
# Copyright 2018 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Contract Management',
    'version': '10.0.4.0.0',
    'category': 'Contract Management',
    'license': 'AGPL-3',
    'author': "OpenERP SA, "
              "Tecnativa, "
              "LasLabs, "
              "Therp BV, "
              "Odoo Community Association (OCA)",
    'website': 'https://github.com/oca/contract',
    'depends': [
        'base',
        'account',
        'analytic'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/contract_security.xml',
        'report/report_contract.xml',
        'report/contract_views.xml',
        'data/contract_cron.xml',
        'data/mail_template.xml',
        'views/contract.xml',
        'views/account_invoice.xml',
        'views/res_partner.xml',
        'views/menu.xml',
    ],
    'installable': True,
}
