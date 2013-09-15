# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from report import report_sxw
from osv import osv
import pooler
import convertion

class account_print_invoice(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_print_invoice, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'total_text':self.total_text,
            'printed_test':self.printed_test,
        })
    def total_text(self,montant):
            devis = 'ARIARY'   
            text=convertion.trad(montant,devis)
            #print inv_obj.name
            #res=inv_obj.write(self.cr, self.uid,self.id,{'printed':True})
            #text=text[1:].capitalize()
            return text   
            
    def printed_test(self,invoice):
            sql="UPDATE account_invoice set printed=True where id=%d" % (invoice.id)
            self.cr.execute(sql)
            res = self.cr.commit()
            return 'True'
            
        
report_sxw.report_sxw(
    'report.account.invoice',
    'account.invoice',
    'addons/account/report/account_print_invoice.rml',
    parser=account_print_invoice
)
report_sxw.report_sxw(
    'report.account.invoice.ref',
    'account.invoice',
    'addons/account/report/account_print_invoice.rml',
    parser=account_print_invoice
)
report_sxw.report_sxw(
    'report.account.invoice.divers',
    'account.invoice',
    'addons/account/report/account_print_invoice.rml',
    parser=account_print_invoice
)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
report_sxw.report_sxw(
    'report.account.invoice.quote',
    'account.invoice',
    'addons/account/report/account_print_invoice.rml',
    parser=account_print_invoice
)

report_sxw.report_sxw(
    'report.account.invoice.avoir',
    'account.invoice',
    'addons/account/report/account_print_invoice.rml',
    parser=account_print_invoice
)
report_sxw.report_sxw(
    'report.account.invoice.pm',
    'account.invoice',
    'addons/account/report/account_print_invoice.rml',
    parser=account_print_invoice
)
report_sxw.report_sxw(
    'report.account.invoice.apercu',
    'account.invoice',
    'addons/account/report/account_print_invoice.rml',
    parser=account_print_invoice
)

report_sxw.report_sxw(
    'report.account.invoice.traite.ech',
    'account.invoice',
    'addons/account/report/account_print_invoice.rml',
    parser=account_print_invoice
)

report_sxw.report_sxw(
    'report.account.invoice.traite',
    'account.invoice',
    'addons/account/report/account_print_invoice.rml',
    parser=account_print_invoice
)

report_sxw.report_sxw(
    'report.account.invoice.traite.blanc',
    'account.invoice',
    'addons/account/report/account_print_invoice.rml',
    parser=account_print_invoice
)
report_sxw.report_sxw(
    'report.account.invoice.notededebit',
    'account.invoice',
    'addons/account/report/account_print_invoice.rml',
    parser=account_print_invoice
)