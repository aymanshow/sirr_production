# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import xmlrpclib
import base64
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
import convertion
from osv import fields, osv, orm
import netsvc
from tools.translate import _
from tools.translate import _
import ir
import netsvc
from mx import DateTime

logger = netsvc.Logger()

class load_clock(osv.osv_memory):
    _name='load.clock'
    _columns ={
    'fichier':fields.binary('Fichier Pointeuse'),
    }

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {}
        attendance_obj=self.pool.get('hr.attendance')
        employee_obj=self.pool.get('hr.employee')
        fichier=self.browse(cr,uid,ids)[0].fichier
        file_content_decoded=base64.decodestring(fichier)
        logger.notifyChannel('fichier:', netsvc.LOG_INFO, file_content_decoded)
        lines=file_content_decoded.splitlines()
        created_ids=[]
        for line in lines:
            fields=line.split()
            count=0
            date=''
            flag=False
            for field in fields:
                count+=1
                if count==3:
                    emp=employee_obj.search(cr,uid,[('matricule','=',field)])
                if count==8:
                    if field=='0':
                        flag=True
                if flag==False:
                    if count==8:
                        date=field
                    if count==9:
                        date+=' '+field
                else:
                    if count==9:
                        date=field
                    if count==10:
                        date+=' '+field                
                logger.notifyChannel('count:', netsvc.LOG_INFO, count)
                logger.notifyChannel('field:', netsvc.LOG_INFO, field)
            logger.notifyChannel('date:', netsvc.LOG_INFO, date)
            
                
                
            if len(emp)>0:
                eid=emp[0]
                att=attendance_obj.create(cr,uid,{'name':date,'employee_id':eid,'action':'sign_in'})
                created_ids.append(att)
        datas['ids']=created_ids
        return {
            'type': 'ir.actions.window',
            'report_name': 'hr.attendance',
            'datas': datas,
        }    
load_clock()


class print_voucher_cash(osv.osv_memory):
    _name='print.account.voucher.cash'
    _columns ={
    'date_from':fields.date('Debut'),
    'date_to':fields.date('Fin'),
    'journal_id':fields.many2many('account.journal','rel_account_report_journal','a_journal_id','b_journal_id','Journaux'),
    'partner_id':fields.many2one('res.partner','A Exclure'),
    }

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {}
        invoice_obj=self.pool.get('account.voucher')
        journal_obj=self.pool.get('account.journal')        
        date_from=self.browse(cr,uid,ids)[0].date_from
        date_to=self.browse(cr,uid,ids)[0].date_to
        partner_id=self.browse(cr,uid,ids)[0].partner_id

        journals=[]
        for journal in self.browse(cr,uid,ids)[0].journal_id:
            journals.append(journal.id)
        inv_ids=invoice_obj.search(cr,uid,[('date','<=',date_to),('date','>=',date_from),('journal_id','in',journals),('type','=','receipt'),('journal_id.type','=','cash'),('partner_id','!=',partner_id.id)],order='journal_id')
        cheques=invoice_obj.search(cr,uid,[('journal_id','in',journals),('type','=','receipt'),('journal_id.type','=','bank'),('reconciled','=',True),('partner_id','!=',partner_id.id)],order='journal_id')
        cheques=invoice_obj.browse(cr,uid,cheques)
        for cheque in cheques:
            if cheque.move_ids != []:
                for move_id in cheque.move_ids:
                    if move_id.account_id == cheque.journal_id.default_credit_account_id or move_id.account_id==cheque.journal_id.x_temporary_account:
                        if move_id.reconcile_id:
                            if move_id.reconcile_id.create_date<=date_to:
                                if move_id.reconcile_id.create_date>=date_from:
                                    inv_ids.append(cheque.id)
        datas['ids']=inv_ids
        #datas=[]
        # for journal in journals:
            # amount=0
            # for voucher in invoice_obj.browse(cr,uid,inv_ids):
                # if voucher.journal_id.id==journal:
                    # amount+=voucher.amount
            # dat={
                # 'journal':journal_obj.browse(cr,uid,[journal])[0].name,
                # 'amount':amount
            # }
            # datas.append(dat)
        logger.notifyChannel('ids:', netsvc.LOG_INFO, datas)  
        #logger.notifyChannel('ids:', netsvc.LOG_INFO, ids)          
        #logger.notifyChannel('datas:', netsvc.LOG_INFO, datas['ids'])        
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.voucher.cash',
            'datas': datas,
        }    
print_voucher_cash()

class print_account_report_gl(osv.osv_memory):
    _name='print.account.report.gl'
    _columns ={
    'date_from':fields.date('Debut'),
    'date_to':fields.date('Fin'),
    'account_id':fields.many2many('account.account','rel_account_report_account','a_account_id','b_account_id','Comptes'),
    }

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {}
        invoice_obj=self.pool.get('account.report.gl')
        date_from=self.browse(cr,uid,ids)[0].date_from
        date_to=self.browse(cr,uid,ids)[0].date_to
        accounts=[]
        for account in self.browse(cr,uid,ids)[0].account_id:
            accounts.append(account.id)
        inv_ids=invoice_obj.search(cr,uid,[('date','<=',date_to),('date','>=',date_from),('account_id','in',accounts)])
        if len(accounts)>1:
            sql = """
            SELECT id
                FROM account_report_gl where date <= '%s' and date >= '%s' and account_id in %s"""% (date_to,date_from,tuple(accounts))
        else:
            sql = """
            SELECT id
                FROM account_report_gl where date <= '%s' and date >= '%s' and account_id = %s"""% (date_to,date_from,accounts[0])
        cr.execute(sql)
        inv_ids = map(lambda x1: x1[0], cr.fetchall())     
        datas['ids']=inv_ids
        logger.notifyChannel('ids:', netsvc.LOG_INFO, inv_ids)  
        #logger.notifyChannel('ids:', netsvc.LOG_INFO, ids)          
        #logger.notifyChannel('datas:', netsvc.LOG_INFO, datas['ids'])        
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.report.gl.gl',
            'datas': datas,
        }    
print_account_report_gl()


class day_invoice(osv.osv_memory):
    _name = "day.invoice"
    _columns = {
    'date': fields.date('Date de debut'),
    'date_to': fields.date('Date de fin'),
    'partner_id':fields.many2one('res.partner','Client')
    
    }

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {}
        invoice_obj=self.pool.get('account.invoice')
        date=self.browse(cr,uid,ids)[0].date
        date_end=self.browse(cr,uid,ids)[0].date_to
        partner_id=self.browse(cr,uid,ids)[0].partner_id
        # logger.notifyChannel('partner_id:', netsvc.LOG_INFO, partner_id)  
        # logger.notifyChannel('date:', netsvc.LOG_INFO, date_end)  
        
        if not partner_id:
            if date_end!=False:
                inv_ids=invoice_obj.search(cr,uid,[('date_invoice','>=',date),('date_invoice','<=',date_end),('type','in',['out_invoice','out_refund']),('state','in',['open','paid'])])
            else:    
                inv_ids=invoice_obj.search(cr,uid,[('date_invoice','=',date),('type','in',['out_invoice','out_refund']),('state','in',['open','paid'])])
        else:
            partner_id=[partner_id.id]
            if date_end!=False:
                inv_ids=invoice_obj.search(cr,uid,[('date_invoice','>=',date),('date_invoice','<=',date_end),('type','in',['out_invoice','out_refund']),('state','in',['open','paid']),('partner_id','in',partner_id)])
            else:
                inv_ids=invoice_obj.search(cr,uid,[('date_invoice','=',date),('type','in',['out_invoice','out_refund']),('state','in',['open','paid']),('partner_id','in',partner_id)])
        shops=[]
        #inv_ids=invoice_obj.search(cr,uid,[('date_invoice','=',date),('type','in',['out_invoice','out_refund']),('state','in',['open','paid'])])        
        invoices=invoice_obj.browse(cr,uid,inv_ids)
        for invoice in invoices:
            if invoice.user_id.shop.id not in shops:
                shops.append(invoice.user_id.shop.id)
        sorted_inv_ids=[]
        for shop in shops:
            for invoice in invoices:
                if invoice.id not in sorted_inv_ids:
                    if invoice.user_id.shop.id==shop:
                        sorted_inv_ids.append(invoice.id)
        datas['ids']=sorted_inv_ids
        #logger.notifyChannel('date:', netsvc.LOG_INFO, date)  
        #logger.notifyChannel('ids:', netsvc.LOG_INFO, ids)          
        #logger.notifyChannel('datas:', netsvc.LOG_INFO, datas['ids'])        
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.invoice.jour',
            'datas': datas,
        }

day_invoice()

class financial_position(osv.osv_memory):
    _name = "financial.position"
    _columns = {
    'date': fields.date('Date Arret'),
    'location_id':fields.many2one('stock.location','Emplacement')
    
    }

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {}
        date=self.browse(cr,uid,ids)[0].date
        location_id=self.browse(cr,uid,ids)[0].location_id
        context.update({'location':location_id})        
        prods=self.pool.get('product.product').search(cr,uid,[])
        prods=self.pool.get('product.product').browse(cr,uid,prods)
        if location_id!=False:
            context['location']=location_id.name
        if date != False:
            context['date_to']=date
        context['date']= date or date_to
        context['journal_id']=False
        location_id
        ids=[]
        datas['stock']=0
        
        inv_obj = self.pool.get('account.move.line')
        states = ['posted','valid']
        
        title = _("Impayes clients - ")
     
        ids = []
        moveline_obj = self.pool.get('account.move.line')
#parametres
        comptes_clients=0
        valeur_stock=0
        portefeuille=0
        datas={}
#comptes clients
        movelines2 = moveline_obj.search(cr, uid,
            [#('partner_id', '=', partner.id),
                ('journal_id.type','in',['sale','sale_refund']),
                ('date','<=',DateTime.strptime(date, '%Y-%m-%d')),
                ('state', 'not in', ['cancel','draft']), 
                ('account_id.type', 'in', ['receivable', 'payable']),
                ('account_id.reconcile','=',True)]) 
                
        movelines2 = moveline_obj.browse(cr,uid,movelines2)
        lines=movelines2
        for y in lines:
            if not y.reconcile_id and not y.reconcile_partial_id:
                comptes_clients=comptes_clients+y.debit-y.credit
            if y.reconcile_id:
                for rec_line in y.reconcile_id.line_id:
                    if rec_line.date>=date and rec_line.state not in ('cancel','draft'):
                        comptes_clients=comptes_clients+y.debit-y.credit
            if y.reconcile_partial_id:
                for rec_line in y.reconcile_partial_id.line_id:
                    if rec_line.date>=date and rec_line.state not in ('cancel','draft'):
                        comptes_clients=comptes_clients+y.debit-y.credit  
#valorisation stock
        product_obj = self.pool.get('product.product')
        products=product_obj.search(cr,uid,[])
        products=product_obj.browse(cr,uid,products,context={'location':location_id.name,'to_date':date})
        for prod in products:
            if prod.virtual_available>0:
                valeur_stock+=prod.virtual_available*prod.standard_price
#portefeuille
        voucher_obj = self.pool.get('account.voucher')
        vouchers=voucher_obj.search(cr,uid,[('type','=','receipt'),('journal_id.x_portefeuille','=',True),('date','<=',DateTime.strptime(date[:10], '%Y-%m-%d'))])
        vouchers=voucher_obj.browse(cr,uid,vouchers)
        for voucher in vouchers:
            if voucher.reconciled:
                if voucher.banking_date<=DateTime.strptime(date[:10], '%Y-%m-%d'):
                    portefeuille+=voucher.amount
            else:
                if not voucher.banking_bank:
                    portefeuille+=voucher.amount
            
        datas['comptes_clients']=comptes_clients
        datas['stock']=valeur_stock
        datas['portefeuille']=portefeuille
        datas['date']=date
        datas['ids']=[1]
        
        
        # logger.notifyChannel('context:', netsvc.LOG_INFO, context)  
        #logger.notifyChannel('ids:', netsvc.LOG_INFO, ids)          
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'product.product.financial',
            'datas': datas,
            'context':context
        }

financial_position()

class product_sonde(osv.osv_memory):
    _name = "product.sonde"
    _columns = {
    'date': fields.date('Date de debut'),
    'date_to': fields.date('Date de fin'),
    'location_id':fields.many2one('stock.location','Emplacement')
    
    }

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {}
        date_to=self.browse(cr,uid,ids)[0].date_to
        date=self.browse(cr,uid,ids)[0].date
        location_id=self.browse(cr,uid,ids)[0].location_id
        context.update({'location':location_id})        
        prods=self.pool.get('product.product').search(cr,uid,[])
        prods=self.pool.get('product.product').browse(cr,uid,prods)
        if location_id!=False:
            context['location']=location_id.name
        if date_to != False:
            context['date_to']=date_to
        if date != False:
            context['date_from']=date
        context['date']= date or date_to
        context['journal_id']=False
        context['mis_en_banque']=False
        ids=[]
        for prod in prods:
            if prod.stock_compare_id.date>=date and prod.stock_compare_id.date<=date_to:
                ids.append(prod.id)        
        datas['ids']=ids
        
        
        # logger.notifyChannel('context:', netsvc.LOG_INFO, context)  
        #logger.notifyChannel('ids:', netsvc.LOG_INFO, ids)          
        #logger.notifyChannel('datas:', netsvc.LOG_INFO, datas['ids'])        
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'product.product.sonde',
            'datas': datas,
            'context':context
        }

product_sonde()

class product_location(osv.osv_memory):
    _name = "product.location"
    _columns = {
    'date': fields.datetime('Date de debut'),
    'date_to': fields.datetime('Date de fin'),
    'location_id':fields.many2one('stock.location','Emplacement')
    
    }

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {}
        date_to=self.browse(cr,uid,ids)[0].date_to
        date=self.browse(cr,uid,ids)[0].date
        location_id=self.browse(cr,uid,ids)[0].location_id
        
        if location_id!=False:
            context['location']=location_id.name
        if date_to != False:
            context['to_date']=date_to
        if date != False:
            context['from_date']=date
        context['date']= date or date_to
        context['journal_id']=False
        context['mis_en_banque']=False
        datas['ids']=[1]
        
        
        # logger.notifyChannel('context:', netsvc.LOG_INFO, context)  
        #logger.notifyChannel('ids:', netsvc.LOG_INFO, ids)          
        #logger.notifyChannel('datas:', netsvc.LOG_INFO, datas['ids'])        
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'product.product.location',
            'datas': datas,
            'context':context
        }

product_location()

class product_order(osv.osv_memory):
    _name = "product.order"
    _columns = {
    'date': fields.datetime('Date de debut'),
    'date_to': fields.datetime('Date de fin'),
    'location_id':fields.many2one('stock.location','Emplacement')
    
    }

    def print_report(self, cr, uid, ids, context=None):
        proc_obj=self.pool.get('procurement.order')
        orderpoint_obj = self.pool.get('stock.warehouse.orderpoint')
        location_obj = self.pool.get('stock.location')
        procurement_obj = self.pool.get('procurement.order')
        request_obj = self.pool.get('res.request')
	product_obj=self.pool.get('product.product')
        wf_service = netsvc.LocalService("workflow")
        view_id=[]
        ids = orderpoint_obj.search(cr, uid, [])
        for op in orderpoint_obj.browse(cr, uid, ids, context=context):
            # if op.procurement_id.state != 'exception':
                # if op.procurement_id and op.procurement_id.purchase_id and op.procurement_id.purchase_id.state in ('draft', 'confirmed'):
                    # continue
            prods = location_obj._product_virtual_get(cr, uid,
                    op.location_id.id, [op.product_id.id],
                    {'uom': op.product_uom.id})[op.product_id.id]
	    ctx=context
            ctx.update({'location':'Arrivage'})
            arrivage=product_obj.browse(cr,uid,[op.product_id.id],context=ctx)
            arrivage=arrivage[0].virtual_available
            logger.notifyChannel('prods:', netsvc.LOG_INFO, prods) 
            if prods < op.product_min_qty:
                qty = max(op.product_min_qty, op.product_max_qty)-prods-arrivage

                reste = qty % op.qty_multiple
                if reste > 0:
                    qty += op.qty_multiple - reste

                newdate = datetime.today() + relativedelta(
                        days = int(op.product_id.seller_delay))
                if qty <= 0:
                    continue
                if op.product_id.type not in ('consu'):
                    if op.procurement_draft_ids:
                    # Check draft procurement related to this order point
                        pro_ids = [x.id for x in op.procurement_draft_ids]
                        cr.execute('select id, product_qty from procurement_order where id in %s order by product_qty desc', (tuple(pro_ids), ))
                        procure_datas = cr.dictfetchall()
                        to_generate = qty
                        for proc_data in procure_datas:
                            if to_generate >= proc_data['product_qty']:
                                wf_service.trg_validate(uid, 'procurement.order', proc_data['id'], 'button_confirm', cr)
                                procurement_obj.write(cr, uid, [proc_data['id']],  {'origin': op.name}, context=context)
                                to_generate -= proc_data['product_qty']
                            if not to_generate:
                                break
                        qty = to_generate

                if qty:
                    proc_id = procurement_obj.create(cr, uid, {
                        'name': op.name,
                        'date_planned': newdate.strftime('%Y-%m-%d'),
                        'product_id': op.product_id.id,
                        'product_qty': qty,
                        'product_uom': op.product_uom.id,
                        'location_id': op.location_id.id,
                        'procure_method': 'make_to_order',
                        'origin': op.name
                    })
                    view_id.append(proc_id)
                    wf_service.trg_validate(uid, 'procurement.order', proc_id,
                            'button_confirm', cr)
                    wf_service.trg_validate(uid, 'procurement.order', proc_id,
                            'button_check', cr)
                    orderpoint_obj.write(cr, uid, [op.id],
                            {'procurement_id': proc_id}, context=context)        
        
        
         
        #logger.notifyChannel('ids:', netsvc.LOG_INFO, ids)          
        #logger.notifyChannel('datas:', netsvc.LOG_INFO, datas['ids'])  
        return {
            'name':_("Reappros"),
            'view_mode': 'tree',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'procurement.order',
            'res_id': view_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context
        }    

product_order()

class bank_status(osv.osv_memory):
    _name = "bank.status"
    _columns = {
    'date': fields.date('Date'),
    'journal_id':fields.many2one('account.journal','Compte'),
    'valeur':fields.float('Valeur internet',),
    'bank_id':fields.many2one('res.bank','Banque')
    }

    def print_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        datas = {}
        banks=[]
        datas['ids']=[124545]        
        invoice_obj=self.pool.get('account.invoice')
        voucher_obj=self.pool.get('account.voucher')
        state_date=self.browse(cr,uid,ids)[0].date
        bank=self.browse(cr,uid,ids)[0].bank_id
        context['date']=state_date
        context['valeur']=self.browse(cr,uid,ids)[0].valeur
        #mis en banque
        vouchers=voucher_obj.search(cr,uid,[('banking_date','=',state_date),('banking_bank','=',bank.id)])
        vouchers=voucher_obj.browse(cr,uid,vouchers)
        mis_en_banque=0
        for voucher in vouchers:
            mis_en_banque+=voucher.amount
        #emises non credites
        vouchers=voucher_obj.search(cr,uid,[('date','=',state_date),('instrument_bank','=',bank.id),('type','=','payment'),('reconciled','=',False)])
        vouchers=voucher_obj.browse(cr,uid,vouchers)
        emises=0
        for voucher in vouchers:
            emises+=voucher.amount
            
        context['journal_id']=self.browse(cr,uid,ids)[0].journal_id.name
        context['mis_en_banque']=mis_en_banque
        
        # logger.notifyChannel('ids:', netsvc.LOG_INFO, context['journal_id'])          
        #logger.notifyChannel('datas:', netsvc.LOG_INFO, datas['ids'])        
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'bank.status',
            'context':context,
            'datas': datas,
        }

bank_status()

class purchase_order(osv.osv):
    _inherit = 'purchase.order'
    
    def get_shop(self, cr, uid, ids):
        user=self.pool.get('res.users').browse(cr,uid,uid)
        if user.shop.name=='Importation':
            return user.shop.name
        else:
            return 'Locaux'
    
    _columns = {
        'order_line': fields.one2many('purchase.order.line', 'order_id', 'Order Lines', readonly=True, states={'draft': [('readonly', False)],'start': [('readonly', False)]}),
        'create':fields.many2one('res.users', 'Demandeur'),
        'daf':fields.many2one('res.users', 'Direction Financiere'),
        'dg':fields.many2one('res.users', 'Direction Generale'),
        'sb':fields.many2one('res.users', 'Direction Commerciale'),
        'date_daf':fields.date('Date Appr. DAF'),
        'date_dg':fields.date('Date Appr. DG'),
        'date_sb':fields.date('Date Appr. SB'),
        'ref':fields.char('Reference Commande', size=64),
        'cur_rate':fields.float('Cours Devise'),
        'containers':fields.float('Conteneurs'),
        'estimated_freight':fields.float('Meilleur taux de fret Estimatif'),
        'incoterm':fields.many2one('stock.incoterms', 'Incoterm'),
        'product_origin':fields.many2one('res.country', 'Origine'),
        'shop_id': fields.many2one('sale.shop', 'Souche', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'payment_term': fields.many2one('account.payment.term', 'Condition de Reglement'),
        
    }
    
    def ceni_create(self,cr,uid,ids,*args):
        username = 'admin' #the user
        pwd = 'ceniltd1*'      #the password of the user
        dbname = 'ceni3'    #the database
        # Get the uid
        sock_common = xmlrpclib.ServerProxy ('http://aozielceniltd.homelinux.org:8069/xmlrpc/common')
        user = sock_common.login(dbname, username, pwd)
        #replace localhost with the address of the server
        sock = xmlrpclib.ServerProxy('http://aozielceniltd.homelinux.org:8069/xmlrpc/object')
        # create missing products
        context={'lang':'fr_FR'}
	for po in self.browse(cr,uid,ids,context=context):
            arg=[('name','like',po.order_line[0].product_id.product_brand_id.name[:10])]
            supplier = sock.execute(dbname, user, pwd, 'res.partner', 'search', arg)
            if not supplier:
                raise osv.except_osv(_('Erruer !'), _('Fournisseur doit etre cree') )      
            else:
                supplier_id=supplier[0]
            arg=[('name','=','Smoi')]                
            customer = sock.execute(dbname, user, pwd, 'res.partner', 'search', arg)
            customer_data=sock.execute(dbname, user, pwd, 'res.partner', 'read', customer,['id','property_product_pricelist',])
            arg=[('partner_id','=',customer[0])] 
            address=sock.execute(dbname, user, pwd, 'res.partner.address', 'search', arg)
            po_name=po.name+' '+po.order_line[0].product_id.product_brand_id.name
            sale_order_data={
            'partner_id':customer[0],
            'partner_order_id':address[0],
            'partner_invoice_id':address[0],
            'partner_shipping_id':address[0],
            'pricelist_id':customer_data[0]['property_product_pricelist'][0],
            'client_order_ref':po_name}
            sale_order=sock.execute(dbname, user, pwd, 'sale.order', 'create', sale_order_data)
            sale_order_lines=[]
            for po_line in po.order_line:   
                line={}
                product=po_line.product_id
                default_code=product.default_code
                description=product.name
                supplier=product.product_brand_id.name
                supplier_ref=product.supplier_ref
                description=description.split()
                clean1=[]
                clean2=[]
                for d in description:
                    if d!=supplier:
                        clean1.append(d)
                for d in clean1:
                    if d!=supplier_ref:
                        clean2.append(d)
                description=' '.join(clean2)
                
                arg=[('default_code','=',default_code)]
                products_found = sock.execute(dbname, user, pwd, 'product.product', 'search', arg)
                if not products_found:
                    arg=[('x_supplier_code','=',supplier_ref)]                
                    products_found_new = sock.execute(dbname, user, pwd, 'product.product', 'search', arg)
                    if not products_found_new:
                        product={
                        'default_code':default_code,
                        'name':description,
                        'x_supplier_code':supplier_ref,
                        'standard_price':po_line.price_unit*(100-po.x_majoration)/100,
                        'list_price':0,
                        'x_origine':po.product_origin.id
                        }
                        prod=sock.execute(dbname, user, pwd, 'product.product', 'create', product)
                        arg=[('product_id','=',prod)]
                        tmpl_id = sock.execute(dbname, user, pwd, 'product.product', 'read', [prod],['product_tmpl_id'])
                        seller_data={
                        'name':supplier_id,
                        'product_id':tmpl_id[0]['product_tmpl_id'][0],
                        'min_qty':0,
                        'product_code':supplier_ref,
                        }
                        seller=sock.execute(dbname, user, pwd, 'product.supplierinfo', 'create', seller_data)
                        line['product_id']=prod
                    else:
                        line['product_id']=products_found_new[0]
                        values={'default_code':default_code}
                        prod= sock.execute(dbname, user, pwd, 'product.product', 'write', [products_found_new[0]], values)
                else:
                    line['product_id']=products_found[0]
                line['product_uom_qty']=po_line.product_qty
                line['name']=po_line.product_id.name
                line['order_id']=sale_order
                line['price_unit']=po_line.price_unit
                
                sale_order_lines.append(line)
            # create purchase order lines
            for ln in sale_order_lines:
                sol=sock.execute(dbname, user, pwd, 'sale.order.line', 'create', ln)
        return True
        
    def apply_increase(self,cr,uid,ids,*args):
        po_line=self.pool.get('purchase.order.line')
        po_obj=self.pool.get('purchase.order')
        for po in po_obj.browse(cr,uid,ids):
            for line in po.order_line:
                pu=line.price_unit
                po_line.write(cr,uid,line.id,{'price_unit':pu*(100+po.x_majoration)/100})
	return True

    def apply_last_price(self,cr,uid,ids,*args):
        po_line=self.pool.get('purchase.order.line')
        po_obj=self.pool.get('purchase.order')
        for po in po_obj.browse(cr,uid,ids):
            for line in po.order_line:
                pu=line.last_price
                po_line.write(cr,uid,line.id,{'price_unit':pu})
	return True

    def get_product_info(self,cr,uid,ids,*args):
	po_line=self.pool.get('purchase.order.line')
	po_obj=self.pool.get('purchase.order')
	prod_obj=self.pool.get('product.product')
	sale_obj=self.pool.get('sale.report')
	for po in po_obj.browse(cr,uid,ids):
		for line in po.order_line:
			product_id=line.product_id.id
			x_purchase_price=0
			x_diff=0
			x_stock_dispo=prod_obj.browse(cr,uid,[product_id],context={'location_id':102})[0].virtual_available
			x_last_landing_cost=line.product_id.calculated_cost
			x_sale_price=line.product_id.list_price
			x_sales_6=0
			x_sales_2012=0
			new_price=0
			date6=(datetime.now()+relativedelta(days=-180)).strftime("%Y-%m-%d")
			date12=(datetime.now()+relativedelta(days=-365)).strftime("%Y-%m-%d")
			sales=sale_obj.search(cr,uid,[('product_id','=',product_id),('date','>',date6)])
			sales=sale_obj.read(cr,uid,sales,['product_uom_qty'])
			for sale in sales:
				x_sales_6+=sale['product_uom_qty']
                        #sales=sale_obj.search(cr,uid,[('product_id','=',product_id),('date','>',date12)])
                        sales=sale_obj.search(cr,uid,[('product_id','=',product_id)])

                        sales=sale_obj.read(cr,uid,sales,['product_uom_qty'])
                        for sale in sales:
                                x_sales_2012+=sale['product_uom_qty']


			purchases=po_line.search(cr,uid,[('product_id','=',product_id),('state','not in',['draft','cancel'])])
			for l in po_line.browse(cr,uid,purchases):
				if l.id!=line.id:
					x_purchase_price=l.price_unit
			new_price=line.price_unit
			x_diff=new_price-x_purchase_price
			if x_purchase_price>0:
				x_diff=(x_diff/x_purchase_price)*100
			else:
				x_diff=(x_diff/1)*100
			po_line.write(cr,uid,line.id,{'x_diff':x_diff,
							'x_stock_dispo':x_stock_dispo,
							'x_last_purchase_price':x_purchase_price,
							'x_last_landing_cost':x_last_landing_cost,
							'x_sale_price':x_sale_price,
							'x_sales_6':x_sales_6,
							'x_sales_2012':x_sales_2012})
	return True

    def action_customer_invoice_create(self, cr, uid, ids, *args):
        res = False

        journal_obj = self.pool.get('account.journal')
        for o in self.browse(cr, uid, ids):
            il = []
            todo = []
            for ol in o.order_line:
                todo.append(ol.id)
                if ol.product_id:
                    a = ol.product_id.product_tmpl_id.property_account_income.id
                    if not a:
                        a = ol.product_id.categ_id.property_account_income_categ.id
                    if not a:
                        raise osv.except_osv(_('Error !'), _('There is no expense account defined for this product: "%s" (id:%d)') % (ol.product_id.name, ol.product_id.id,))
                else:
                    a = self.pool.get('ir.property').get(cr, uid, 'property_account_income_categ', 'product.category').id
                fpos = o.fiscal_position or False
                a = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, a)
                il.append(self.inv_line_create(cr, uid, a, ol))

            a = o.client_id.property_account_payable.id
            journal_ids = journal_obj.search(cr, uid, [('type', '=','sale'),('company_id', '=', o.company_id.id)], limit=1)
            if not journal_ids:
                raise osv.except_osv(_('Error !'),
                    _('There is no purchase journal defined for this company: "%s" (id:%d)') % (o.company_id.name, o.company_id.id))
            inv = {
                'name': o.partner_ref or o.name,
                'reference': o.partner_ref or o.name,
                'account_id': a,
                'type': 'out_invoice',
                'partner_id': o.client_id.id,
                'currency_id': o.pricelist_id.currency_id.id,
                'address_invoice_id': self.pool.get('res.partner').address_get(cr, uid, [o.client_id.id], ['default'])['default'],
                'address_contact_id': self.pool.get('res.partner').address_get(cr, uid, [o.client_id.id], ['default'])['default'],
                'journal_id': len(journal_ids) and journal_ids[0] or False,
                'origin': o.name,
                'invoice_line': il,
                'fiscal_position': o.fiscal_position.id or o.client_id.property_account_position.id,
                'payment_term': o.client_id.property_payment_term and o.client_id.property_payment_term.id or False,
                'company_id': o.company_id.id,
            }
            inv_id = self.pool.get('account.invoice').create(cr, uid, inv, {'type':'out_invoice'})
            self.pool.get('account.invoice').button_compute(cr, uid, [inv_id], {'type':'out_invoice'})
            self.write(cr, uid, [o.id], {'invoice_ids': [(4, inv_id)]})
            res = inv_id
        return res
    
    def price_approve(self, cr, uid, ids,
            name=None, args=None, context=None):
        "Return the total quantity in an invoice"
        inv_line_obj = self.pool.get('purchase.order.line')
        prod=self.pool.get('product.product')
        inv_obj = self.browse(cr,uid,ids)
        for lines in inv_obj:
            for line in lines.order_line:
                if not line.product_id:
                    continue
                prod_id=line.product_id.id
                #if line.product_id.standard_price==0:
                prod.write(cr,uid,prod_id,{'standard_price':line.x_new_cost})                
                prod.write(cr,uid,prod_id,{'calculated_cost':line.x_new_cost})
                if line.x_new_sale_price>0:
                    prod.write(cr,uid,prod_id,{'list_price':line.x_new_sale_price})
        return True

    def insert_seller(self, cr, uid, ids,
            name=None, args=None, context=None):
        "Set supplier"
        inv_line_obj = self.pool.get('purchase.order.line')
        prod=self.pool.get('product.product')
        inv_obj = self.browse(cr,uid,ids)
        for lines in inv_obj:
            for line in lines.order_line:
                if not line.product_id:
                    continue
                prod_id=line.product_id.id
                prod.write(cr,uid,prod_id,{'seller_ids':[(0,0,{'name':line.partner_id.id,'delay':1,'min_qty':0})]})
        return True

        
    def check_min_stock(self,cr, uid, ids, *args):
        prod_obj=self.pool.get('product.product')
        purchase_obj=self.pool.get('purchase.order')
        orderpoint_obj=self.pool.get('stock.warehouse.orderpoint')
        mini=True
        for order in purchase_obj.browse(cr,uid,ids):
            for line in order.order_line:
                if line.product_id and line.product_id.procure_method!='make_to_order':
                    orderpoints=orderpoint_obj.search(cr,uid,[('product_id','=',line.product_id.id)])
                    #print 'order_points',orderpoints
                    if orderpoints==[]:
                        raise osv.except_osv(_('Warning'), _("Veuillez inserer la regle du stock minimum pour %s! \n\n Misaotra")%(line.product_id.name))
                        mini=False
                        return False
                    elif not line.product_id.seller_ids:
                        raise osv.except_osv(_('Warning'), _("Veuillez inserer le fournisseur pour %s! \n\n Misaotra")%(line.product_id.name))
                        mini=False
                        return False                    
        return mini
                        
    
    
    def onchange_partner_id(self, cr, uid, ids, part):

        if not part:
            return {'value':{'partner_address_id': False, 'fiscal_position': False}}
        addr = self.pool.get('res.partner').address_get(cr, uid, [part], ['default'])
        part = self.pool.get('res.partner').browse(cr, uid, part)
        pricelist = part.property_product_pricelist_purchase.id
        fiscal_position = part.property_account_position and part.property_account_position.id or False
        payment_term = part.property_payment_term and part.property_payment_term.id or False
        return {'value':{'partner_address_id': addr['default'], 'pricelist_id': pricelist, 'fiscal_position': fiscal_position,'payment_term':payment_term}}
    
    _defaults = {
        'create': lambda obj, cr, uid, context: uid,
        #'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, obj.get_shop(cr,uid,obj)),
    }
    def merge_procurement(self, cr, uid, ids=False):
        purchase_obj=self.pool.get('purchase.order')
        product_obj=self.pool.get('product.product')
        purchases=purchase_obj.search(cr,uid,[('origin','like','OP%'),('state','=','draft')])
        purchase_orders=purchase_obj.browse(cr,uid,purchases)
        suppliers=[]
        purchase_ids=[]
        brands=[]
        for order in purchase_orders:
            suppliers.append(order.partner_id.id)
            for ol in order.order_line:
		brands.append(ol.product_id.product_brand_id.id)
        suppliers=list(set(suppliers))
	brands=list(set(brands))
        orders=[]
	for brand in brands:
	    prods=product_obj.search(cr,uid,[('product_brand_id','=',brand)])
            for supplier in suppliers:
                purchases=purchase_obj.search(cr,uid,[('origin','like','OP%'),('state','=','draft'),('partner_id','=',supplier),('product_id','in',prods)])
		orders.append(purchases)
        for order in orders:
            emailto=['sebastien.roux@groupe-smtp.com']
            merged_order=purchase_obj.do_merge(cr,uid,order)
            subject='Commande '
            date=time.strftime('%Y-%m-%d')
            rep=[]
            rep.append([('purchase.order.discount'),[merged_order]])
            self.pool.get('email.smtpclient').send_email(cr,uid,1,emailto,subject,'',[],[rep])
            logger.notifyChannel('merge:', netsvc.LOG_INFO, merged_order)   
        return True
    def send_procurement(self, cr, uid, ids=False):
        purchase_obj=self.pool.get('purchase.order')
        purchases=purchase_obj.search(cr,uid,[('origin','like','OP%'),('state','=','draft')])
        for purchase in purchases:
            emailto=['sebastien.roux@groupe-smtp.com']
            subject='Commande '
            date=time.strftime('%Y-%m-%d')
            rep=[]
            rep.append([('report.purchase.order.test'),[purchase]])
            self.pool.get('email.smtpclient').send_email(cr,uid,1,emailto,subject,'',[],rep)
  
purchase_order()

class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'
    _columns = {
        'nomenclature': fields.related('product_id','nomenclature', type='many2one', relation='product.nomenclature', string='Nomenclature'),
    }
    def onchange_discount_purchase(self,cr,uid,ids,disc,unit_price):
        res={}
        return {'value':{'x_unit_discount': (unit_price*((100-disc)/100)) }}
purchase_order_line()

class sale_order(osv.osv):
    _inherit = 'sale.order'
    _columns = {
        'create':fields.many2one('res.users', 'Vendeur'),
        'validate':fields.many2one('res.users', 'Dir. Com.'),
        'date_create':fields.date('Date Creation'),
        'date_validate':fields.date('Date Appr. DC'),
        'name_divers':fields.char('Nom Occasionel', size=64),
        'tel_divers':fields.char('Telephone Occasionel', size=64),
        'address_divers':fields.char('Addresse Occasionel', size=64),
        'cheque':fields.boolean('Paiement Cheque?')
    }
    
    _defaults = {
        'create': lambda obj, cr, uid, context: uid,
    }

    def update_discount(self, cr,uid,ids,context=None):
        so_obj=self.pool.get('sale.order')
        sol_obj=self.pool.get('sale.order.line')
        to_update=[]
        for order in self.browse(cr,uid,ids):
            for line in order.order_line:
                to_update.append(line.id)
        logger.notifyChannel('SALE ORDER IDS:', netsvc.LOG_INFO, to_update)
        logger.notifyChannel('discount:', netsvc.LOG_INFO, order.x_global_discount)
        sol_obj.write(cr,uid,to_update,{'discount':order.x_global_discount})
        return True

    def create_mo(self, cr, uid, ids, context=None):
        """ Make Manufacturing(production) order from procurement
        @return: New created Production Orders procurement wise 
        """
        res = {}
        company = self.pool.get('res.users').browse(cr, uid, uid, context).company_id
        production_obj = self.pool.get('mrp.production')
        move_obj = self.pool.get('stock.move')
        order_line_obj=self.pool.get('sale.order.line')
        sale_obj = self.browse(cr,uid,ids)
        bom_obj=self.pool.get('mrp.bom')
        for order in self.browse(cr, uid, ids, context={}):
            proc_ids = []
            output_id = order.shop_id.warehouse_id.lot_output_id.id
            picking_id = False
            for line in order.order_line:
                date_planned = datetime.now() + relativedelta(days=line.delay or 0.0)

                move_id = False
                if not order.x_enlevement:
                    raise osv.except_osv(_('Warning'), _("Veuillez preciser l'enlevement SVP! \n Misotra"))
                if line.product_id and line.product_id.product_tmpl_id.type in ('product', 'consu'):
                    location_id = order.shop_id.warehouse_id.lot_stock_id.id
                    if line.location:
                        location_id=line.location.id
                    bom_ids=bom_obj.search(cr,uid,[('product_id','=',line.product_id.id)])
                    #bom_id=bom_obj.browse(cr,uid,bom_ids)[0]
                    newdate = date_planned
                    if order.name_divers:
                        partner_name=order.name_divers
                    else:
                        partner_name=order.partner_id.name
                    bill=0
                    for bom in bom_obj.browse(cr,uid,bom_ids):
                        if bom.id:
                            bill=bom.id
                        else:
                            bill=0
                    if bill!=0 and not line.x_of:
                        produce_id = production_obj.create(cr, uid, {
                        'origin': order.name + partner_name ,
                        'x_sale_order':order.id,
                        'x_res_partner':order.partner_id.id,
                        'x_notes':line.notes,
                        'product_id': line.product_id.id,
                        'product_qty': line.product_uos_qty,
                        'th_weight':line.th_weight,
                        'product_uom': line.product_uom.id,
                        'product_uos_qty': line.product_uos and line.product_uos_qty or False,
                        'product_uos': line.product_uos and line.product_uos.id or False,
                        'location_src_id': 65,
                        'location_dest_id': order.x_enlevement.x_finished.id,
                        'bom_id': bill,
                        'company_id': order.company_id.id,
                    })
                        order_line_obj.write(cr,uid,line.id,{'x_of':True})
                    
                    if not picking_id:
                        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.internal')
                        picking_id = self.pool.get('stock.picking').create(cr, uid, {
                            'name': pick_name,
                            'origin': 'PROD :' + order.name+ ' - ' + partner_name,
                            'type': 'internal',
                            'state': 'draft',
                            'move_type': order.picking_policy,
                            'address_id': order.partner_shipping_id.id,
                            'note': order.note,
                            'invoice_state': 'none',
                            'company_id': order.company_id.id,
                        })                        
                    move_id = self.pool.get('stock.move').create(cr, uid, {
                        'name': line.name[:64],
                        'picking_id': picking_id,
                        'product_id': line.product_id.id,
                        'date': date_planned,
                        'date_expected': date_planned,
                        'product_qty': line.product_uos_qty,
                        'product_uom': line.product_uom.id,
                        'product_uos_qty': line.product_uos_qty,
                        'product_uos': (line.product_uos and line.product_uos.id)\
                                or line.product_uom.id,
                        'product_packaging': line.product_packaging.id,
                        'address_id': line.address_allotment_id.id or order.partner_shipping_id.id,
                        'location_id': order.x_enlevement.x_finished.id,
                        'location_dest_id': order.x_enlevement.x_route.id,
                        'x_th_weight':line.th_weight,
                        'tracking_id': False,
                        'state': 'draft',
                        'note': line.notes,
                        'company_id': order.company_id.id,
                    })
            self.pool.get('sale.order').write(cr,uid,[order.id],{'x_of':True})

        return True

    def create_picking(self, cr, uid, ids, context=None):
        """ Make Manufacturing(production) order from procurement
        @return: New created Production Orders procurement wise 
        """
        res = {}
        company = self.pool.get('res.users').browse(cr, uid, uid, context).company_id
        production_obj = self.pool.get('mrp.production')
        move_obj = self.pool.get('stock.move')
        sale_obj = self.browse(cr,uid,ids)
        bom_obj=self.pool.get('mrp.bom')
        for order in self.browse(cr, uid, ids, context={}):
            proc_ids = []
            output_id = order.shop_id.warehouse_id.lot_output_id.id
            picking_id = False
            for line in order.order_line:
                date_planned = datetime.now() + relativedelta(days=line.delay or 0.0)

                move_id = False
                if not order.x_enlevement:
                    raise osv.except_osv(_('Warning'), _("Veuillez preciser l'enlevement SVP! \n Misotra"))
                    
                    if not picking_id:
                        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.internal')
                        picking_id = self.pool.get('stock.picking').create(cr, uid, {
                            'name': pick_name,
                            'origin': 'Commande Client :' + order.name+ ' - ' + partner_name,
                            'type': 'internal',
                            'state': 'draft',
                            'move_type': order.picking_policy,
                            'address_id': order.partner_shipping_id.id,
                            'note': order.note,
                            'invoice_state': 'none',
                            'company_id': order.company_id.id,
                        })                        
                    move_id = self.pool.get('stock.move').create(cr, uid, {
                        'name': line.name[:64],
                        'picking_id': picking_id,
                        'product_id': line.product_id.id,
                        'date': date_planned,
                        'date_expected': date_planned,
                        'product_qty': line.product_uos_qty,
                        'product_uom': line.product_uom.id,
                        'product_uos_qty': line.product_uos_qty,
                        'product_uos': (line.product_uos and line.product_uos.id)\
                                or line.product_uom.id,
                        'product_packaging': line.product_packaging.id,
                        'address_id': line.address_allotment_id.id or order.partner_shipping_id.id,
                        'location_id': order.x_enlevement.x_source.id,
                        'location_dest_id': order.x_enlevement.x_route.id,
                        'x_th_weight':line.th_weight,
                        'tracking_id': False,
                        'state': 'draft',
                        'note': line.notes,
                        'company_id': order.company_id.id,
                    })
            sale_obj.write(cr,uid,order.id,{'x_of':True})

        return True
        
    def message_new(self, cr, uid, msg, context=None):
        """
        Automatically calls when new email message arrives

        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks
        """
        mailgate_pool = self.pool.get('email.server.tools')

        subject = msg.get('subject')
        body = msg.get('body')
        msg_from = msg.get('from')
        priority = msg.get('priority')


        if msg.get('priority', False):
            vals['priority'] = priority

        res = mailgate_pool.get_partner(cr, uid, msg.get('from') or msg.get_unixfrom())
        vals = {
            'name': subject,
            'email_from': msg_from,
            'email_cc': msg.get('cc'),
            'description': body,
            'user_id': False,
            'partner_id':res.id,
        }        
        if res:
            vals.update(res)
        if subject=='BC':
            for line in body.splitlines():
                item=line.split(',')
                logger.notifyChannel('body', netsvc.LOG_INFO, item[0])
            res = self.create(cr, uid, vals, context)
        else:
            logger.notifyChannel('Echec Reception:', netsvc.LOG_INFO, msg_from)
        
        return res

        
    
sale_order()

class procurement_order(osv.osv):
    _inherit = 'procurement.order'
    _columns = {
        'th_weight':fields.float('M. Lineare'),
    }
procurement_order()

class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    _columns = {
        'th_weight':fields.float('M. Lineare'),
    }
mrp_production()


class excel_reports(osv.osv):
    _name = 'excel.reports'
    _description ='Excel Reports'
    _columns = {
        'name':fields.char('Description',size=64),
        'report':fields.binary('Rapport'),

    }
excel_reports()


class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    _columns = {
        'location':fields.many2one('stock.location', 'Emplacement'),
    }
    def getlocation(self, cr, uid, ids, loc):
        res={}
        cur_user=self.pool.get('res.users').browse(cr,uid,uid)
        shop=cur_user.shop.name
        shop='%'+shop+'%'
        current_loc=loc
        locations=self.pool.get('stock.location').search(cr,uid,[('location_id.name','like',shop)])
        if current_loc in locations:
            return {'value':{'location': loc}}
        else:
            for id in ids:
                return {'value':{'location': locations[0]}}
        return {'value':{'location': locations[0]}}
    def product_discount_change(self, cr, uid, ids, discount,max,product_id,price_unit):
        warning={}
        if discount>max:
            warning = {
                    'title': _('Remise incorrect !'),
                    'message': _('Remise Maximum atteint!!!') 
            }
        user_obj=self.pool.get('res.users')
        user=user_obj.browse(cr,uid,uid)
        if user.x_discount:
            if user.x_discount>0:
                max=user.x_discount
#        logger.notifyChannel('product:', netsvc.LOG_INFO, product_id)
       	if product_id:
		product_id=self.pool.get('product.product').browse(cr,uid,product_id)
#       		logger.notifyChannel('product price:', netsvc.LOG_INFO, product_id.lst_price)
#       		logger.notifyChannel('order line PU:', netsvc.LOG_INFO, price_unit)        
       		if product_id.lst_price>price_unit:
        		max=0
        discount=min(discount,max)   
        return {'value':{'discount': discount},'warning':warning}
        
    def onchange_price_unit(self, cr, uid, ids, pricelist,product,qty,uom,partner_id,date_order,price_unit):
        warning={}
        price=price_unit
        if product:
            price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                product, qty or 1.0, partner_id, {
                    'uom': uom,
                    'date': date_order,
                    })[pricelist]
        
        if price is False:
            warning = {
                'title': 'No valid pricelist line found !',
                'message':
                    "Couldn't find a pricelist line matching this product and quantity.\n"
                    "You have to change either the product, the quantity or the pricelist."
                }
        if price_unit<price:
            warning = {
                    'title': _('Prix incorrect !'),
                    'message': _('Peux pas dimunuer les prix atteint!!!') 
            }
        prix=max(price,price_unit)   
        if product:
            return {'value':{'price_unit': prix},'warning':warning}
        else:
            pass
            
sale_order_line()


class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    def change_cheque_account(self,cr,uid,ids,journal_id):
        # print 'Checking'
        voucher=self.pool.get('account.voucher')
        move=self.pool.get('account.move.line')
        journal=self.pool.get('account.journal')
        journal=journal.browse(cr,uid,journal_id)
        voucher_line=self.pool.get('account.voucher.line')
        res={}
        for line in self.browse(cr, uid, ids):
            for move_line in line.move_ids:
                if journal.x_temporary_account and move_line.account_id==journal.default_credit_account_id:
                    #print move_line.id  
                    #print move_line.account_id
                    #print journal.x_temporary_account.id
                    recs = []
                    recs += [move_line.id]
                    state=move_line.state
                    # move.write(cr,uid,recs,{'state':'draft'})
                    sql="UPDATE account_move_line set account_id=%d where id=%d" % (journal.x_temporary_account.id,move_line.id)
                    cr.execute(sql)
                    res2 = cr.commit()                    
                    # move.write(cr,uid,recs,{'account_id':journal.x_temporary_account.id,'state':state})
                    return{'value':res} 
        return{'value':res} 
        
    def onchange_bank_date(self,cr,uid,ids,date):
        res={}
        for line in self.browse(cr, uid, ids):
            ds = datetime.strptime(line.date, '%Y-%m-%d')
            if date<ds:
                return{'value':{'banking_date':ds}}
        return {}
        
    def button_cheque_account(self,cr,uid,ids,context=None):
        #print 'clicked'
        voucher=self.pool.get('account.voucher')
        move=self.pool.get('account.move.line')
        journal=self.pool.get('account.journal')
        voucher_line=self.pool.get('account.voucher.line')
        res={}
        for line in self.browse(cr, uid, ids):
            journal_id=line.journal_id.id
            journal=journal.browse(cr,uid,journal_id)
            for move_line in line.move_ids:
                #print move_line
                #print move_line.id
                if journal.x_temporary_account and move_line.account_id==journal.default_credit_account_id:
                    sql="UPDATE account_move_line set account_id=%d where id=%d" % (journal.x_temporary_account.id,move_line.id)
                    cr.execute(sql)
                    res2 = cr.commit()     
                    return True
        return True       
    def change_cheque_return(self,cr,uid,ids,journal_id):
        voucher=self.pool.get('account.voucher')
        move=self.pool.get('account.move.line')
        journal=self.pool.get('account.journal')
        journal=journal.browse(cr,uid,journal_id)
        voucher_line=self.pool.get('account.voucher.line')
        cheque_return=self.pool.get('cheque.return')
        li=self.browse(cr,uid,ids)[0]
        val = {
            'paiement':li.id,
            'cheque':li.reference,
            'amount':li.amount,
            'partner_id':li.partner_id.id
                }
        cheque_return.create(cr,uid,val)
        res={}
	for line in self.browse(cr, uid, ids):
	    new_voucher=voucher.copy(cr,uid,line.id)
            for move_line in line.move_ids:
                if journal.x_temporary_account and move_line.account_id==journal.x_temporary_account:
                    sql="UPDATE account_move_line set account_id=%d where id=%d" % (journal.default_credit_account_id.id,move_line.id)
                    cr.execute(sql)
                    res2 = cr.commit()   
                    return{'value':res}         
        return{'value':res}         
    def move_line_id_payment_get(self, cr, uid, ids, *args):
        if not ids: return []
        result = self.move_line_id_payment_gets(cr, uid, ids, *args)
        return result.get(ids[0], [])

    def move_line_id_payment_gets(self, cr, uid, ids, *args):
        res = {}
        if not ids: return res
        cr.execute('SELECT i.id, l.id '\
                   'FROM account_move_line l '\
                   'LEFT JOIN account_voucher i ON (i.move_id=l.move_id) '\
                   'WHERE i.id IN %s '\
                   'AND l.account_id=i.account_id',
                   (tuple(ids),))
        for r in cr.fetchall():
            res.setdefault(r[0], [])
            res[r[0]].append( r[1] )
        return res
    def _get_invoice_from_reconcile(self, cr, uid, ids, context=None):
        move = {}
        for r in self.pool.get('account.move.reconcile').browse(cr, uid, ids, context=context):
            for line in r.line_partial_ids:
                move[line.move_id.id] = True
            for line in r.line_id:
                move[line.move_id.id] = True

        invoice_ids = []
        if move:
            invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('move_id','in',move.keys())], context=context)
        return invoice_ids
        
    def test_paid(self, cr, uid, ids, *args):
        res = self.move_line_id_payment_get(cr, uid, ids)
        # print res
        if not res:
            return False
        ok = True
        for id in res:
            cr.execute('select reconcile_id from account_move_line where id=%s', (id,))
            ok = ok and  bool(cr.fetchone()[0])
        return ok
    
    #def _reconciled(self, cr, uid, ids, name, args, context=None):
    #    res = {}
    #    for id in ids:
    #        res[id] = self.test_paid(cr, uid, [id])
    #    return res
    
    def _reconciled(self, cr, uid, ids, field_name, args, context=None):
        if context is None:
            context={}
        result = {}
        for order in self.browse(cr,uid,ids, context=context):
            result[order.id]=False
            if order.move_ids != []:
                for move_id in order.move_ids:
                    if move_id.account_id == order.journal_id.default_credit_account_id or move_id.account_id==order.journal_id.x_temporary_account:
                        if not move_id.reconcile_id:
                            result[order.id]=False
                        else:
                            result[order.id] = True
                            #self.write(cr,uid,order.id,{'check_return':False})
        return result
    
    def deposit_check(self, cr, uid, ids, context=None):             
        self.write(cr, uid, ids, {'state':'check_deposit'})
        return True
        
    def confirm_deposit(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'check_bank'})
        return True

    def action_cancel_check(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'check_return'})
        return True
    def action_check_escompte(self,cr,uid,ids,context=None):
        self.write(cr, uid, ids, {'journal_id':'ESC'})
        self.write(cr, uid, ids, {'account_id':'511400'})
        return True

    _columns = {
        'instrument_type':fields.char('Type', size=64),
        'instrument_date':fields.date('Date'),
        'transmitted':fields.date('Transmis'),
        'to_account':fields.date('Compta'),
        'ref': fields.related('partner_id','ref', type='char', relation='res.partner', string='Code', readonly=1),
        'reconciled': fields.function(_reconciled, method=True,string='Reconciled', type='boolean'),
        'instrument_bank':fields.many2one('res.bank','Banque'),
        'banking_date':fields.date('Mise En Banque'),
        'banking_bank':fields.many2one('res.bank','Banque'),
        'banking_number':fields.char('N° bordereau', size=64),
        'check_return':fields.boolean('Retourné'),
        'balance':fields.float('Balance'),
        'tire':fields.char('Tire', size=64),
        'state':fields.selection(
            [('draft','Draft'),
             ('proforma','Pro-forma'),
             ('check_deposit','En Reglement'),
             ('check_return','Reglement Retourné'),
             ('check_bank','Reglement deposée en banque'),
             ('posted','Posted'),
             ('cancel','Cancel')], 'State', readonly=True, size=32,),
        }       
    
    def onchange_bank(self, cr, uid, ids, move_ids,bank):
        move_lines=self.pool.get('account.move.line')
        for voucher in self.browse(cr, uid, ids):
            recs = []
            for line in voucher.move_ids:
                recs += [line.id]
        move_lines.write(cr, uid, recs,{'bank':bank})
        return True
    def onchange_check_bal(self,cr,uid,ids,partner_id,amount):
        voucher=self.pool.get('account.voucher')
        voucher_line=self.pool.get('account.voucher.line')
        res={}
        total_cr=0
        total_dr=0
        balance=0
        default = {
            'value':{'x_payment_balance':0},
        }
        payment=amount
        transaction=0
        if not partner_id:
            return default
        else:
            for voucher_id in self.browse(cr,uid,ids):
                #print 'entering voucher'
                for v in voucher_id.line_cr_ids:
                    if v.amount!=0:
                        total_cr+=v.amount
                for v in voucher_id.line_dr_ids:
                    if v.amount!=0:
                        total_dr+=v.amount
                transaction=total_cr-total_dr
                #print transaction
        balance=payment-transaction
        res['x_payment_balance']=balance
#        self.write(cr,uid,ids,{'x_payment_balance':balance})
        default['value']={'x_payment_balance':balance}
        # print default
        return default
        #return True
                
    def check_bal(self,cr,uid,ids,context=None):
        voucher=self.pool.get('account.voucher')
        voucher_line=self.pool.get('account.voucher.line')
        res={}
        total_cr=0
        total_dr=0
        for voucher_id in self.browse(cr,uid,ids):
            #print 'Entering'
            payment=voucher_id.amount
            for v in voucher_id.line_cr_ids:
                if v.amount!=0:
                    total_cr+=v.amount
            for v in voucher_id.line_dr_ids:
                if v.amount!=0:
                    total_dr+=v.amount
            transaction=total_cr-total_dr
            balance=payment-transaction
            if balance!=0:
                warn_msg = _("Montant Paye.\t\t:%s\n"
                "Montant Transactions.:%s\n"
                "Balance\t\t\t\t:%s\n") % \
                    (payment,transaction,balance)
                warning = {
                    'title': _('Balance !'),
                    'message': warn_msg
                    }
#	res['x_payment_balance']=balance 
        #print 'out'
        self.write(cr,uid,ids,{'x_payment_balance':balance})
#        return {'value':res}
        return True                
account_voucher()

class account_voucher_line(osv.osv):
    _inherit='account.voucher.line'
    def onchange_move_line_id(self, cr, user, ids, move_line_id,reference,amount,context=None):
        """
        Returns a dict that contains new values and context

        @param move_line_id: latest value from user input for field move_line_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        res = {}
        instrument=reference
        voucher_line=self.pool.get('account.voucher.line')
        #print 'entering smtp_custom_account_voucher'
        move_line_pool = self.pool.get('account.move.line')
        if move_line_id:
            move_line = move_line_pool.browse(cr, user, move_line_id, context=context)
            if move_line.credit:
                ttype = 'dr'
            else:
                ttype = 'cr'
                
            account_id = move_line.account_id.id
            res.update({
                'account_id':account_id,
                'type': ttype, 
            })
        return {
            'value':res,
        } 

    def onchange_payment_amount(self,cr,uid,ids,amount,old_amount,payment):
        voucher=self.pool.get('account.voucher')
        voucher_line=self.pool.get('account.voucher.line')
        res={}
        for line in self.browse(cr, uid, ids):
            voucher_id=line.voucher_id
            current_voucher=voucher.browse(cr,uid,voucher_id)
            voucher_amount=current_voucher.amount
            total_receipts=0
            total_payments=0
            debit_line_amounts=0
            credit_line_amounts=0            
            if amount>line.amount_unreconciled:
                proposed_amount=line.amount_unreconciled
                res['amount']=line.amount_unreconciled
                res['x_old_amount']=res['amount']
            else:
                res['amount']=amount
                res['x_old_amount']=amount
        return{'value':res} 
        
     
account_voucher_line()


class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    def get_po_qty(self,cr,uid,id,product):
        bc=self.x_po.order_line.search(cr,uid,[('product_id','=',product)])
        return bc[0].product_qty
    
    def action_invoice_ship_create(self, cr, uid, ids, *args):
        wf_service = netsvc.LocalService("workflow")
        picking_id = False
        move_obj = self.pool.get('stock.move')
        proc_obj = self.pool.get('procurement.order')
        company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        for order in self.browse(cr, uid, ids, context={}):
            if order.type=='out_invoice' and not order.x_so and not order.origin:
                proc_ids = []
                output_id = self.pool.get('res.users').browse(cr, uid, uid).shop.warehouse_id.lot_output_id.id
                location_id = self.pool.get('res.users').browse(cr, uid, uid).location.id
                picking_id = False
                for line in order.invoice_line:
                    proc_id = False
                    date_planned = datetime.now() + relativedelta(0.0)
                    date_planned= date_planned.strftime('%Y-%m-%d %H:%M:%S')
                    move_id = False
                    if line.product_id and line.product_id.product_tmpl_id.type in ('product', 'consu'):
                        if not picking_id:
                            pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
                            picking_id = self.pool.get('stock.picking').create(cr, uid, {
                                'name': pick_name,
                                'origin': order.number,
                                'type': 'out',
                                'state': 'auto',
                                'move_type': 'direct',
                                'address_id': order.address_invoice_id.id,
                                'invoice_state': 'none',
                                'company_id': order.company_id.id,
                            })
                        move_id = self.pool.get('stock.move').create(cr, uid, {
                            'name': line.name[:64],
                            'discount':line.discount,
                            'picking_id': picking_id,
                            'product_id': line.product_id.id,
                            'date': date_planned,
                            'date_expected': date_planned,
                            'product_qty': line.quantity,
                            'product_uom': line.uos_id.id,
                            'product_uos_qty': line.quantity,
                            'product_uos': line.uos_id.id,
                            'address_id': order.address_invoice_id.id,
                            'location_id': line.location.id or location_id,
                            'location_dest_id': output_id,
                            'tracking_id': False,
                            'state': 'draft',
                            #'state': 'waiting',
                            'company_id': order.company_id.id,
                        })

                        proc_ids.append(proc_id)

                val = {}

                if picking_id:
                    wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)

                #for proc_id in proc_ids:
                #    wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)

                val['shipped'] = False

                self.write(cr, uid, [order.id], val)
        return True


    def get_move_qty(self,cr,uid,id,product):
	bc=self.x_picking_id.move_lines.search(cr,uid,[('product_id','=',product)])
	return bc[0].product_qty

    def check_printed(self,cr,uid,id):
        if self.printed:
            return True
        else:
            sql="UPDATE account_invoice set printed=True where id=%d" % (id)
            self.cr.execute(sql)
            res = self.cr.commit()
            # print '>>>>>>>>>>>>>>>>>>'
            return False
    
    def _check_paid(self, cr, uid, ids, name, args, context=None):
        res={}
        voucher_lines=self.pool.get('account.voucher.line')
        res[id]=True
        return res

    def test_check(self, cr, uid, ids, *args):
        ok = False
        voucher_lines=self.pool.get('account.voucher.line')
        for line in self.browse(cr, uid, ids):
            res=voucher_lines.search(cr, uid, [('name', 'like', line.number), ('instrument_number', '!=', '')])
            if res:
                ok= True
            else:
                ok= False
        return ok
    def test_allowed(self, cr, uid, ids, *args):
        ok = False
        inv=self.pool.get('account.invoice')
        for line in self.browse(cr, uid, ids):
            allowed=line.allow_out
            # print allowed
        return allowed

    def _reconciled_check(self, cr, uid, ids, name, args, context=None):
            res = {}
            for id in ids:
                res[id] = self.test_check(cr, uid, [id])
            return res
    def _check_allow_out(self, cr, uid, ids, name, args, context=None):
            res = {}
            for id in ids:
                res[id] = self.test_allowed(cr, uid, [id])
            return res

    _columns = {
        'check_state': fields.function(_reconciled_check, method=True,string='Reglé', type='boolean'),
        'out_allowed': fields.function(_check_allow_out, method=True, string='Sortie Autorisee', type='boolean'),
        'allow_out': fields.boolean('Autorisation de Sortie'),    
        'transmitted': fields.boolean('Transmis'),    
        'name_divers':fields.char('Nom Occasionel', size=64),
        'tel_divers':fields.char('Telephone Occasionel', size=64),
        'address_divers':fields.char('Addresse Occasionel', size=64),   
        'validator':fields.many2one('res.users','Validation'),
        'printed': fields.boolean('Printed'), 
        'reviens_state':fields.selection(
            [('calculated','Revient Theorique'),
             ('fixed','Prix de vente établie'),
             ('confirmed','Confirmé')], 'Calcul du reviens', readonly=True, size=32,),        
        'cur_rate':fields.float('Cours Devise'),
        }
    _defaults = {
        'cur_rate': 1,
    }

    
    def printed(self,cr,uid,ids,context=None):
        return 'Printing'
        
    def create_card_comm(self,cr,uid,ids,context=None):
        obj_product=self.pool.get('product.product')
        obj_inv_line=self.pool.get('account.invoice.line')
        products=obj_product.search(cr, uid, [('default_code','like','FRAISCB%')])
        products=obj_product.browse(cr,uid,products)
        for inv in self.browse(cr,uid,ids):
            a=inv.user_id.shop.x_journal.default_credit_account_id.id
            ht=inv.amount_untaxed
            for p in products:
                if p.default_code=='FRAISCB':
                    obj_inv_line.create(cr, uid, {
                    'name': p.name,
                    'account_id': a,
                    'price_unit': ht*3.25/100,
                    'th_weight':0,
                    'quantity': 1,
                    'discount':0,
                    'invoice_id':inv.id,
                    'uos_id': p.uom_id.id,
                    'product_id': p.id,
                    'invoice_line_tax_id':[(6,0,[1])],                    
                    'account_analytic_id': False,})
                else:
                    obj_inv_line.create(cr, uid, {
                    'name': p.name,
                    'account_id': a,
                    'price_unit': 1800,
                    'th_weight':0,
                    'quantity': 1,
                    'invoice_id':inv.id,
                    'discount':0,
                    'uos_id': p.uom_id.id,
                    'product_id': p.id,
                    'invoice_line_tax_id':[(6,0,[1])],
                    'account_analytic_id': False,})
        return True
    
account_invoice()

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns ={
        'local_supplier':fields.boolean('Fournisseur Local'),
        'foreign_supplier':fields.boolean('Fournisseur Import'),
        'group_supplier':fields.boolean('Fournisseur Group'), 
    }
 #   _sql_constraints = [ ('name', 'UNIQUE (name)', 'The name of the partner must be unique !')] 
res_partner()

class account_bank_statement_line(osv.osv):
    _inherit = 'account.bank.statement.line'
    _columns ={
        'move_line':fields.many2one('account.move.line'),
    }
 #   _sql_constraints = [ ('name', 'UNIQUE (name)', 'The name of the partner must be unique !')] 
account_bank_statement_line()


class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'

    def product_discount_change(self, cr, uid, ids, discount,max):
        warning={}
        if discount>max:
            warning = {
                    'title': _('Remise incorrect !'),
                    'message': _('Remise Maximum atteint!!!') 
            }
        user_obj=self.pool.get('res.users')
        user=user_obj.browse(cr,uid,uid)
        if user.x_discount:
            if user.x_discount>0:
                max=user.x_discount
#        if self.browse(cr,uid,ids)[0].invoice_id.type=='out_refund':
#            max=100
        discount=min(discount,max)   
        return {'value':{'discount': discount},'warning':warning}
        
    def _product_margin(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = 0
            if line.product_id:
#                if line.product_id.purchase_price:
#                   res[line.id] = round((line.price_unit*line.product_uos_qty*(100.0-line.discount)/100.0) -(line.product_id.purchase_price*line.product_uos_qty), 2)
#                else:
                #if line.inv_id.journal_id.name=='%Financier%':
                #    res[line.id] = round((line.price_unit*line.quantity*(100.0-line.discount)/100.0) -(line.product_id.standard_price*line.quantity), 2)*-1
                    
                res[line.id] = round((line.price_unit*line.quantity*(100.0-line.discount)/100.0) -(line.product_id.standard_price*line.quantity), 2)
                
        return res
    def _product_margin_perc(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = 0
            if line.product_id:
#                if line.purchase_price:
#                    res[line.id] = (round(((line.price_unit*line.product_uos_qty*(100.0-line.discount)/100.0) -(line.product_id.purchase_price*line.product_uos_qty))/(line.price_unit*line.product_uos_qty*(100.0-line.discount)/100.0), 2))*100
#                else:
                # print line.margin
                # print line.price_unit*line.quantity*(100.0-line.discount)/100.0
                res[line.id] = (round(line.margin/max(0.01,(line.price_unit*line.quantity*(100.0-line.discount)/100.0)), 2))*100
   
        return res
        
        
    _columns ={
	'marge':fields.float('old_marge'),
        'th_weight':fields.float('M. Linere'),
        'margin': fields.function(_product_margin, type='float', method=True, string='Marge',store=True),
        'margin_perc': fields.function(_product_margin_perc, type='float',method=True, string='% Mar',store=True),
        'location':fields.many2one('stock.location','Emplacement'),

    }

    def onchange_discount_purchase(self,cr,uid,ids,disc,unit_price):
        res={}
        discount=disc
        warning={}
        if disc>0:
            if self.browse(cr,uid,ids)[0].invoice_id.type=='out_invoice':
		if not self.browse(cr,uid,ids)[0].invoice_id.x_override_promo:
                    if self.browse(cr,uid,ids)[0].product_id.list_price > self.browse(cr,uid,ids)[0].price_unit:
                        discount=0
                        warning = {
                                'title': _('Remise incorrect !'),
                                'message': _('Produit en Promo!!!') 
                        }                   
                    else:
                        warning={}
                        user_obj=self.pool.get('res.users')
                        user=user_obj.browse(cr,uid,uid)
                        max=10
                        if user.x_discount:
                            if user.x_discount>0:
                                max=user.x_discount
                        if discount>max:
                            warning = {
                                'title': _('Remise incorrect !'),
                                'message': _('Remise Maximum atteint!!!') 
                            }                    
        #            max=100
                else:
                    warning={}
                    user_obj=self.pool.get('res.users')
                    user=user_obj.browse(cr,uid,uid)
                    max=10
                    if user.x_discount:
                        if user.x_discount>0:
                            max=user.x_discount
                    if discount>max:
                        warning = {
                            'title': _('Remise incorrect !'),
                            'message': _('Remise Maximum atteint!!!')
                        }

                discount=min(discount,max) 
        return {'value':{'x_unit_discount': (unit_price*((100-disc)/100)),'discount':discount },'warning':warning}
        
        #   _sql_constraints = [ ('name', 'UNIQUE (name)', 'The name of the partner must be unique !')] 
account_invoice_line()

class product_brand(osv.osv):
    _name = "product.brand"
    _description = "Branding"
    _columns={
        'name':fields.char('Marque',size=64),
}
product_brand()

class product_nomenclature(osv.osv):
    _name = "product.nomenclature"
    _description = "Nomenclature"
    _columns={
        'name':fields.char('Nomenclature',size=64),
	'description':fields.char('Description',size=128),
        'custom1':fields.float('Droit Douane'),
        'custom2':fields.float('TVA'),
        'custom3':fields.float('Droit Assisea'),
}
product_nomenclature()


class product_product(osv.osv):
    _inherit = 'product.product'
    _columns ={
        'prix1':fields.float('Prix 1'),
        'prix2':fields.float('Prix 2'),
        'prix3':fields.float('Prix 3'),
        'prix4':fields.float('Prix 4'),
        'prix5':fields.float('Prix 5'),
        'prix6':fields.float('Prix 6'),
        'prix7':fields.float('Prix 7'),
        'prix8':fields.float('Prix 8'),
        'prix9':fields.float('Prix 9'),
        'prix10':fields.float('Prix 10'),
        'prix11':fields.float('Prix 11'),
        'marque':fields.many2one('product.brand', 'Marque'),
	'nomenclature':fields.many2one('product.nomenclature','Nomenclature')
    }
    _sql_constraints = [('ref','unique(ref)', 'Unique!')]
product_product()

class res_company(osv.osv):
    _inherit = 'res.company'
    
    _columns = {
        'local_purchase':fields.char('local_purchase',store=True, size=64),
        'import_purchase':fields.char('import_purchase',store=True, size=64),
    }
res_company()


class account_move_line(osv.osv):
    _inherit = 'account.move.line'

    def _amount_residual(self, cr, uid, ids, field_names, args, context=None):
        """
           This function returns the residual amount on a receivable or payable account.move.line.
           By default, it returns an amount in the currency of this journal entry (maybe different
           of the company currency), but if you pass 'residual_in_company_currency' = True in the
           context then the returned amount will be in company currency.
        """
        res = {}
        if context is None:
            context = {}
        cur_obj = self.pool.get('res.currency')
        for move_line in self.browse(cr, uid, ids, context=context):
            res[move_line.id] = {
                'amount_residual': 0.0,
                'amount_residual_currency': 0.0,
                'amount_balance':0,
            }

            if move_line.reconcile_id:
                continue
            if not move_line.account_id.type in ('payable', 'receivable'):
                #this function does not suport to be used on move lines not related to payable or receivable accounts
                continue

            if move_line.currency_id:
                move_line_total = move_line.amount_currency
                sign = move_line.amount_currency < 0 and -1 or 1
            else:
                move_line_total = move_line.debit - move_line.credit
                sign = (move_line.debit - move_line.credit) < 0 and -1 or 1
            line_total_in_company_currency =  move_line.debit - move_line.credit
            context_unreconciled = context.copy()
	    amount_bal=line_total_in_company_currency
            if move_line.reconcile_partial_id:
                for payment_line in move_line.reconcile_partial_id.line_partial_ids:
                    if payment_line.id == move_line.id:
                        continue
                    if payment_line.currency_id and move_line.currency_id and payment_line.currency_id.id == move_line.currency_id.id:
                            move_line_total += payment_line.amount_currency
                    else:
                        if move_line.currency_id:
                            context_unreconciled.update({'date': payment_line.date})
                            amount_in_foreign_currency = cur_obj.compute(cr, uid, move_line.company_id.currency_id.id, move_line.currency_id.id, (payment_line.debit - payment_line.credit), round=False, context=context_unreconciled)
                            move_line_total += amount_in_foreign_currency
                        else:
                            move_line_total += (payment_line.debit - payment_line.credit)
                    line_total_in_company_currency += (payment_line.debit - payment_line.credit)
		    if payment_line.credit!=0:
	            	amount_bal=line_total_in_company_currency

            result = move_line_total
            res[move_line.id]['amount_residual_currency'] =  sign * (move_line.currency_id and self.pool.get('res.currency').round(cr, uid, move_line.currency_id, result) or result)
            res[move_line.id]['amount_residual'] = sign * line_total_in_company_currency
            res[move_line.id]['amount_balance']= amount_bal
            #print res[move_line.id]['amount_balance'] 
        return res
    
    
    _columns = {
        'instrument_number':fields.char('Instrument', size=64),
        'bank': fields.many2one('res.bank','Banque'),
        'amount_balance': fields.function(_amount_residual, method=True, string='Solde', multi="residual"),
    }
account_move_line()

class account_move(osv.osv):
    _inherit = 'account.move'
    
    _columns = {
        'ref': fields.char('Reference', size=64,fnct_search=True),
        }
account_move()


class res_users(osv.osv):
    _inherit = 'res.users'
    _columns = {
        'location':fields.many2one('stock.location','Emplacement'),
        'shop':fields.many2one('sale.shop','Souche'),
    }
res_users()

class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    _columns = {
        'validator':fields.many2one('res.users', 'Validation'),
    }
    def set_draft(self, cr, uid, ids,
            name=None, args=None, context=None):
        pickings = self.browse(cr,uid,ids)
        move=self.pool.get('stock.move')
        picking=self.pool.get('stock.picking')        
        for pick in pickings:
            for move_line in pick.move_lines:
                move.write(cr,uid,move_line.id,{'state':'confirmed'})
            picking.write(cr,uid,pick.id,{'state':'assigned'})
        return True
                
    
    def set_location(self, cr, uid, ids,
            name=None, args=None, context=None):
        "Return the total quantity in an invoice"
        prod=self.pool.get('product.product')
        move=self.pool.get('stock.move')
        picking=self.pool.get('stock.picking')
        pickings = self.browse(cr,uid,ids)
        for picking in pickings:
            for move_line in picking.move_lines:
                if not move_line.product_id:
                    continue
                # line.product_id.calculated_cost=l
                # if line.x_move_id:
                if "Arrivage" in move_line.location_dest_id.name:
                    dest=move_line.location_dest_id.chained_location_id.id
                    move.write(cr,uid,move_line.id,{'location_dest_id':dest})
        return True
    def set_force_location(self, cr, uid, ids,
            name=None, args=None, context=None):
        "Return the total quantity in an invoice"
        prod=self.pool.get('product.product')
        move=self.pool.get('stock.move')
        picking=self.pool.get('stock.picking')
        pickings = self.browse(cr,uid,ids)
        for picking in pickings:
            for move_line in picking.move_lines:
                if not move_line.product_id:
                    continue
                # line.product_id.calculated_cost=l
                # if line.x_move_id:
                dest=picking.x_force_destination.id
                move.write(cr,uid,move_line.id,{'location_dest_id':dest})
        return True
        
    def picking_validate(self, cursor, user, ids, args, context=None):
        self.write(cursor, user, ids, {'validator': user})

        warning={}
        warning = {
                'title': _('Validation'),
                'message': _('Document Valide par %s'% user)
        }
	return True	
       # return {'value':{'validator':user}}
stock_picking()

class stock_location(osv.osv):
    _inherit='stock.location'
    
    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        if context:
	    # print 'context',context
            if context.get('shop',False):
                cur_user=self.pool.get('res.users').browse(cr,user,user)
                shop=cur_user.shop.name
                shop='%'+shop+'%'
		# print shop
                return self.pool.get('stock.location').search(cr,user,[('location_id.name','like',shop)])
                #return super(stock_location,self).search(cr, user, args, offset, limit, order,context, count)
            else:
                return super(stock_location,self).search(cr, user, args, offset, limit, order,context, count)
        else:
            return super(stock_location,self).search(cr, user, args, offset, limit, order,context, count)
        
stock_location()

class mrp_production_confirm_old(osv.osv_memory):
    """
    This wizard will confirm the all the selected draft invoices
    """

    _name = "mrp.production.confirm"
    _description = "Confirmer les Ordres de Fabrication"

    def mrp_production_confirm(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService('workflow')
        if context is None:
            context = {}
        pool_obj = pooler.get_pool(cr.dbname)
        data_inv = pool_obj.get('mrp.production').read(cr, uid, context['active_ids'], ['state'], context=context)

        for record in data_inv:
            if record['state']!= 'draft':
                raise osv.except_osv(_('Warning'), _("Validation Impossible!"))
            wf_service.trg_validate(uid, 'mrp.production', record['id'], 'button_confirm', cr)
        return {'type': 'ir.actions.act_window_close'}

mrp_production_confirm_old()

