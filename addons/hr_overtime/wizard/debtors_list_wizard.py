# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2003-2010 NS-Team (<http://www.ns-team.fr>).
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

import wizard
import pooler
import datetime
from datetime import date
from mx import DateTime
from tools.translate import _

debtors_list_form = '''<?xml version="1.0"?>
<form string="Impayes Clients">
    <group col="8">
        <group col="2">
        </group>
        <group col="2">
            <field name="code"/>
        </group>
        <group col="4">
            <group colspan="4"  attrs="{'invisible': [('period','=','s')]}">
                <group colspan="2">
                    <field name="year"/>
                </group>
                <group colspan="2" >
                    <field name="month" attrs="{'invisible': [('period','=','a')]}"/>
                </group>
            </group>
            <group colspan="4">
                <field name="invoice_date_debut"/>
                <field name="invoice_date_fin"/>
                
                <field name="ech"/>
            </group>
            <field name="partner_id"/>
            <field name="detail"/>
            <field name="paid"/>
            <field name="douteux"/>
            <field name="categ_doubtful_id"/>
        </group>
    </group>
</form>'''


debtors_list_fields = {
        'period': {'string':'Period', 'type':'selection', 'selection':[('m','Month'),('a','Year'),('s','Selection')]},
        'month': {'string':'Month', 'type':'selection', 'selection':[('1','January'),('2','February'),('3','March'),('4','April'),('5','May'),('6','June'),('7','July'),('8','August'),('9','September'),('10','October'),('11','November'),('12','December')]},
        'year': {'string':'Year', 'type':'selection', 'selection':[('2008','2008'),('2009','2009'),('2010','2010'),('2011','2001'),('2012','2012'),('2013','2013'),('2014','2014'),('2015','2015')]},
        'date_from': {'string':'From', 'type':'date'},
        'invoice_date_debut': {'string':'Date de Facture de', 'type':'date'},
        'invoice_date_fin': {'string':'Date de Facture a', 'type':'date'},
        'ech': {'string':'Echeance', 'type':'date'},        
        'maturity': {'string':'Date de Echeance <=', 'type':'date'},        
        'partner_id': {'string':'Client', 'type':'many2one','relation':'res.partner'},
        'categ_doubtful_id': {'string':'Niveau Douteux', 'type':'many2one','relation':'res.partner.category'},
        'detail':{'string':'Montrer Details?','type':'boolean'},
        'paid':{'string':'Inclure payees?','type':'boolean'},
        'douteux':{'string':'Seulement Douteux','type':'boolean'},
        'code':{'string':'Code Client','type':'char'},
    }


class wizard_debtors_list(wizard.interface):

    def _get_defaults(self, cr, uid, data, context={}):
        now=datetime.datetime.now()
        now= datetime.date(now.year, now.month, 1) - datetime.timedelta(days=1) # previous month
        data['form']['period'] = 's'
        data['form']['month'] = str(now.month)
        data['form']['year'] = str(now.year)
        data['form']['ech'] = '2100-01-01'        
        return data['form']
        
    def _get_states(self, cr, uid, data, context):
        return 'print_report_c'
            
    def _get_records(self, cr, uid, data, context={}):
        inv_obj = pooler.get_pool(cr.dbname).get('account.move.line')
        voucher_obj = pooler.get_pool(cr.dbname).get('account.voucher')

        states = ['posted','valid']
        
        title = _("Impayes clients - ")
     
        ids = []
        # print inv_ids
        partner_id=data['form']['partner_id']
        moveline_obj = pooler.get_pool(cr.dbname).get('account.move.line')
        #conditions de date
        if data['form']['invoice_date_fin']!='':
            invoice_date_fin= DateTime.strptime(data['form']['invoice_date_fin'], '%Y-%m-%d') 
        else:
            invoice_date_fin='2030-01-01'

        if data['form']['invoice_date_debut']!='':
            invoice_date_debut= DateTime.strptime(data['form']['invoice_date_debut'], '%Y-%m-%d') 
        else:
            invoice_date_debut='1990-01-01'

        maturity_date= DateTime.strptime(data['form']['ech'], '%Y-%m-%d') 
        print maturity_date
        print invoice_date_fin
        # print partners
        if data['form']['partner_id']:
            movelines = moveline_obj.search(cr, uid,
                [('partner_id', '=', partner_id),('journal_id.type','in',['sale','sale_refund']),
                    ('date','<=',invoice_date),
                    ('account_id.type', 'in', ['receivable', 'payable']),
                    ('state', '<>', 'draft'), ('reconcile_id', '=', False),('account_id.reconcile','=',True)])
        elif data['form']['code']:
            partners=pooler.get_pool(cr.dbname).get('res.partner').search(cr,uid,[('ref','like','%'+data['form']['code']+'%')])
            movelines = moveline_obj.search(cr, uid,
                [('partner_id', 'in', partners),('journal_id.type','in',['sale','sale_refund']),
                    ('date','<=',invoice_date_fin),
                    ('date','>=',invoice_date_debut),
                    ('account_id.type', 'in', ['receivable', 'payable']),
                    ('state', '<>', 'draft'), ('reconcile_id', '=', False),('account_id.reconcile','=',True)])
        else:
            # print 't'
            if(data['form']['ech']!='2100-01-01'):
	            movelines = moveline_obj.search(cr, uid,
	                [#('partner_id', '=', partner.id),
                    ('journal_id.type','in',['sale','sale_refund']),
                    ('date','<=',data['form']['invoice_date_fin']),
                    ('date','>=',data['form']['invoice_date_debut']), 
                    ('date_maturity','<',data['form']['ech']),                                        
                    ('account_id.type', 'in', ['receivable', 'payable']),
                    ('state', '<>', 'draft'), ('reconcile_id', '=', False),('account_id.reconcile','=',True)])
            else:
                movelines = moveline_obj.search(cr, uid,
                [#('partner_id', '=', partner.id),
                    ('journal_id.type','in',['sale','sale_refund']),
                    ('date','<=',data['form']['invoice_date_fin']),
                    ('date','>=',data['form']['invoice_date_debut']),
                    # ('date_maturity','<',data['form']['ech']),                 
                    ('account_id.type', 'in', ['receivable', 'payable']),
                    ('state', '<>', 'draft'), 
                    ('account_id.type', 'in', ['receivable', 'payable']),
                    ('state', '<>', 'draft'), ('reconcile_id', '=', False),('account_id.reconcile','=',True)]) 
                    
        amount=0
        if (data['form']['paid'])!=0:
            paid=True
            movelines2 = moveline_obj.search(cr, uid,
                [#('partner_id', '=', partner.id),
                    ('journal_id.type','in',['sale','sale_refund']),
                    ('date','<=',data['form']['invoice_date_fin']),
                    ('date','>=',data['form']['invoice_date_debut']),
                    ('state', '<>', 'draft'), ('reconcile_id', '!=', False),
                    ('account_id.type', 'in', ['receivable', 'payable']),
                    ('state', '<>', 'draft'),('account_id.reconcile','=',True)]) 
                    
            movelines2 = moveline_obj.browse(cr,uid,movelines2)

            lines=movelines2
            for y in lines:
                #if not y.reconcile_id and not y.reconcile_partial_id:
                #    ids.append(x.id)
                #if y.reconcile_id:
                #    for rec_line in y.reconcile_id.line_id:
                #        if rec_line.date<=data['form']['invoice_date_fin'] and rec_line.state not in ('cancel','draft'):
                #            ids.append(rec_line.id)
                #if y.reconcile_partial_id:
                #    for rec_line in y.reconcile_partial_id.line_id:
                #        if rec_line.date<=data['form']['invoice_date_fin'] and rec_line.state not in ('cancel','draft'):
                #            ids.append(rec_line.id)                
                if y.reconcile_id.line_id[0].date>=data['form']['invoice_date_fin']:
                    amount=amount+y.debit-y.credit
                    ids.append(y.id)
        else:
            paid=False
        vouchers = voucher_obj.search(cr, uid,
                [#                    ('account_id.user_type.code','in',['receivable','payable']),
                 ('check_return', '=', True),('state','not in',['draft','cancel'])])

        vouchers=voucher_obj.browse(cr,uid,vouchers)
        for voucher in vouchers:
            moves=voucher.move_ids
            for move in moves:
                if move.debit>0:
                    movelines.append(move.id)

        movelines = moveline_obj.browse(cr, uid, movelines)
        
        if movelines:
            lines=movelines
            for x in lines:
                amount=amount+x.debit*x.credit
                if data['form']['douteux']==True:
                    if x.partner_id.x_doubtful:
                        if data['form']['categ_doubtful_id']:
			    if x.partner_id.x_categ_doubtful_id.id==data['form']['categ_doubtful_id']:
                                ids.append(x.id)
                        else:
                            ids.append(x.id)
                else:
                    if data['form']['categ_doubtful_id']:
                        if x.partner_id.x_categ_doubtful_id.id==data['form']['categ_doubtful_id']:
                            ids.append(x.id)
                    else:
                        ids.append(x.id)

                # print 'id2-------------------',ids
        #770,470,476
        
                
        print 'AMOUNT------------',amount
        title+=_(" ")
        if data['form']['detail']==0:
            detail=False
        else:
            detail=True
        if data['form']['paid']==0:
            paid=False
        else:
            paid=True
            
        return {'ids' : ids , 'title' : title, 'period' : data['form']['period'],
                'detail' : detail,'paid' : paid, 'year':data['form']['year']} 
        
    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {
                'type': 'form',
                'arch':debtors_list_form,
                'fields':debtors_list_fields,
                'state':[('end','Cancel'),('nextstate','Print')]
            },
        },
        'nextstate' : {
            'actions' : [],
            'result' : {'type' : 'choice', 'next_state' : _get_states}
        },
# This can be used to select various king of report presentation
#        'print_report_f': {
#            'actions': [_get_records],
#            'result': {
#                'type': 'print',
#                'name' : 'Revenue per product by ...',
#                'report': 'ns_sales_reports.liste_factures_produits_f',
#                'rml' : 'ns_sales_reports/report/liste_factures_produits_f.jrxml',
#                'state': 'end'
#            },
#        },
        'print_report_c': {
            'actions': [_get_records],
            'result': {
                'type': 'print',
                'name' : 'Journal Caisse',
                'report': 'report.debtors_list',
                'rml' : 'ns_sales_reports/report/debtors_list.jrxml',
                'state': 'end'
            },
        },
    }

wizard_debtors_list('report.debtors_list.wizard')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
