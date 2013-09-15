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

from osv import fields, osv
from tools.translate import _
import netsvc

class account_invoice_debit(osv.osv_memory):

    """Debits Note from Invoice"""

    _name = "account.invoice.debit"
    _description = "Invoice Debit Note"
    _columns = {
       'date': fields.date('Operation date', help='This date will be used as the invoice date for Refund Invoice and Period will be chosen accordingly!'),
       'period': fields.many2one('account.period', 'Force period'),
       'journal_id': fields.many2one('account.journal', 'Refund Journal', help='You can select here the journal to use for the refund invoice that will be created. If you leave that field empty, it will use the same journal as the current invoice.'),
       'description': fields.char('Description', size=128, required=True),
       'comment': fields.text('Comment', required=True),
    }

    def _get_journal(self, cr, uid, context=None):
        obj_journal = self.pool.get('account.journal')
        if context is None:
            context = {}
        journal = obj_journal.search(cr, uid, [('type', '=', 'sale')])
        if context.get('type', False):
            if context['type'] in ('in_invoice', 'in_refund'):
                journal = obj_journal.search(cr, uid, [('type', '=', 'purchase')])
        return journal and journal[0] or False

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'journal_id': _get_journal,
        'filter_refund': 'modify',
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        journal_obj = self.pool.get('account.journal')
        res = super(account_invoice_debit,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        #Debit note only from customer o purchase invoice
        #type = context.get('journal_type', 'sale_refund')
        type = context.get('journal_type', 'sale')
        if type in ('sale', 'sale_refund'):
            type = 'sale'
        else:
            type = 'purchase'
        for field in res['fields']:
            if field == 'journal_id':
                journal_select = journal_obj._name_search(cr, uid, '', [('type', '=', type)], context=context, limit=None, name_get_uid=1)
                res['fields'][field]['selection'] = journal_select
        return res

    def _get_period(self, cr, uid, context={}):
        """
        Return  default account period value
        """
        account_period_obj = self.pool.get('account.period')
        ids = account_period_obj.find(cr, uid, context=context)
        period_id = False
        if ids:
            period_id = ids[0]
        return period_id

    def _get_orig(self, cr, uid, inv, ref, context={}):
        """
        Return  default origin value
        """
        nro_ref = ref
        if inv.type == 'out_invoice':
            nro_ref = inv.number
        orig = 'FACT:' +(nro_ref or '') + '- DE FECHA:' + (inv.date_invoice or '') + (' TOTAL:' + str(inv.amount_total) or '')
        return orig

    def compute_debit(self, cr, uid, ids, context=None):
        """
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: the account invoice refund’s ID or list of IDs

        """
        inv_obj = self.pool.get('account.invoice')
        reconcile_obj = self.pool.get('account.move.reconcile')
        account_m_line_obj = self.pool.get('account.move.line')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        wf_service = netsvc.LocalService('workflow')
        inv_tax_obj = self.pool.get('account.invoice.tax')
        inv_line_obj = self.pool.get('account.invoice.line')
        res_users_obj = self.pool.get('res.users')
        if context is None:
            context = {}

        for form in  self.read(cr, uid, ids, context=context):
            created_inv = []
            date = False
            period = False
            description = False
            company = res_users_obj.browse(cr, uid, uid, context=context).company_id
            journal_id = form.get('journal_id', False)
            for inv in inv_obj.browse(cr, uid, context.get('active_ids'), context=context):
                if inv.state in ['draft', 'proforma2', 'cancel']:
                    raise osv.except_osv(_('Error !'), _('Can not create a debit note from draft/proforma/cancel invoice.'))
                if inv.reconciled and mode in ('cancel', 'modify'):
                    raise osv.except_osv(_('Error !'), _('Can not create a debit note from invoice which is already reconciled, invoice should be unreconciled first. You can only Refund or Debit this invoice'))
                if inv.type not in ['in_invoice', 'out_invoice']:
                    raise osv.except_osv(_('Error !'), _('Can not make a debit note on a refund invoice.'))
                if form['period']:
                    period = form['period']
                else:
                    #Take period from the current date
                    #period = inv.period_id and inv.period_id.id or False
                    period = self._get_period(cr, uid, context)

                if not journal_id:
                    journal_id = inv.journal_id.id

                if form['date']:
                    date = form['date']
                    if not form['period']:
                            cr.execute("select name from ir_model_fields \
                                            where model = 'account.period' \
                                            and name = 'company_id'")
                            result_query = cr.fetchone()
                            if result_query:
                                #in multi company mode
                                cr.execute("""select p.id from account_fiscalyear y, account_period p where y.id=p.fiscalyear_id \
                                    and date(%s) between p.date_start AND p.date_stop and y.company_id = %s limit 1""", (date, company.id,))
                            else:
                                #in mono company mode
                                cr.execute("""SELECT id
                                        from account_period where date(%s)
                                        between date_start AND  date_stop  \
                                        limit 1 """, (date,))
                            res = cr.fetchone()
                            if res:
                                period = res[0]
                else:
                    #Take current date
                    #date = inv.date_invoice
                    date = time.strftime('%Y-%m-%d')
                if form['description']:
                    description = form['description']
                else:
                    description = inv.name

                if not period:
                    raise osv.except_osv(_('Data Insufficient !'), \
                                            _('No Period found on Invoice!'))

                #we get original data of invoice to create a new invoice that is the copy of the original
                invoice = inv_obj.read(cr, uid, [inv.id],
                            ['name', 'type', 'number', 'reference',
                            'comment', 'date_due', 'partner_id',
                            'address_contact_id', 'address_invoice_id',
                            'partner_insite', 'partner_contact',
                            'partner_ref', 'payment_term', 'account_id',
                            'currency_id', 'invoice_line', 'tax_line',
                            'journal_id', 'period_id'], context=context)
                invoice = invoice[0]
                del invoice['id']
                invoice_lines = []
                tax_lines = []
                #Add origin, parent and comment values
                orig = self._get_orig(cr, uid, inv, invoice['reference'], context)
                invoice.update({
                    'type': inv.type,
                    'date_invoice': date,
                    'state': 'draft',
                    'number': False,
                    'invoice_line': invoice_lines,
                    'tax_line': tax_lines,
                    'period_id': period,
                    'parent_id':inv.id,
                    'name': description,
                    'origin': orig,
                    'comment':form['comment']
                })
                #take the id part of the tuple returned for many2one fields
                for field in ('address_contact_id', 'address_invoice_id', 'partner_id',
                        'account_id', 'currency_id', 'payment_term', 'journal_id'):
                        invoice[field] = invoice[field] and invoice[field][0]
                # create the new invoice
                inv_id = inv_obj.create(cr, uid, invoice, {})
                # we compute due date
                if inv.payment_term.id:
                    data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id], inv.payment_term.id, date)
                    if 'value' in data and data['value']:
                        inv_obj.write(cr, uid, [inv_id], data['value'])
                created_inv.append(inv_id)
            #we get the view id
            if inv.type in ('out_invoice', 'out_refund'):
                xml_id = 'action_invoice_tree1'
            else:
                xml_id = 'action_invoice_tree2'
            #we get the model
            result = mod_obj.get_object_reference(cr, uid, 'account', xml_id)
            id = result and result[1] or False
            # we read the act window
            result = act_obj.read(cr, uid, id, context=context)
            # we add the new invoices into domain list
            invoice_domain = eval(result['domain'])
            invoice_domain.append(('id', 'in', created_inv))
            result['domain'] = invoice_domain
            return result

    def invoice_debit(self, cr, uid, ids, context=None):
        return self.compute_debit(cr, uid, ids, context=context)


account_invoice_debit()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
