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

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from osv import fields, osv

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
        'sb':fields.many2one('res.users', 'Service Budget'),
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
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, obj.get_shop(cr,uid,obj)),
    }
    
purchase_order()

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
    }
    
    _defaults = {
        'create': lambda obj, cr, uid, context: uid,
    }
    
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

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    _columns = {
        'location':fields.many2one('stock.location', 'Emplacement'),
    }
sale_order_line()


class account_voucher(osv.osv):
    _inherit = 'account.voucher'
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
        print res
        print '>>>>>>>>>>>>>>>>>>>>'
        if not res:
            return False
        ok = True
        for id in res:
            cr.execute('select reconcile_id from account_move_line where id=%s', (id,))
            ok = ok and  bool(cr.fetchone()[0])
        return ok
    
    def _reconciled(self, cr, uid, ids, name, args, context=None):
        res = {}
        for id in ids:
            res[id] = self.test_paid(cr, uid, [id])
        return res
    
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
        'ref': fields.related('partner_id','ref', type='char', relation='res.partner', string='Code', readonly=1),
        'reconciled': fields.function(_reconciled, method=True,string='Reconciled', type='boolean'),
        'instrument_bank':fields.many2one('res.bank','Banquue'),
        'banking_date':fields.date('Mise En Banque'),
        'banking_bank':fields.many2one('res.bank','Banquue'),
        'banking_number':fields.char('N° bordereau', size=64),
        'check_return':fields.boolean('Retourné'),
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
account_voucher()

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
            
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
            print allowed
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
        'check_state': fields.function(_reconciled_check, method=True, string='Reglé', type='boolean'),
        'out_allowed': fields.function(_check_allow_out, method=True, string='Sortie Autorisee', type='boolean'),
        'allow_out': fields.boolean('Autorisation de Sortie'),    
        'transmitted': fields.boolean('Transmis'),    
        'name_divers':fields.char('Nom Occasionel', size=64),
        'tel_divers':fields.char('Telephone Occasionel', size=64),
        'address_divers':fields.char('Addresse Occasionel', size=64),   
        'validator':fields.many2one('res.users','Validation'),
        'printed': fields.boolean('Printed'), 
        'reviens_state':fields.selection(
            [('calculated','Calculé'),
             ('fixed','Prix de vente établie'),
             ('confirmed','Confirmé')], 'Calcul du reviens', readonly=True, size=32,),        
        'cur_rate':fields.float('Cours Devise'),
        }
    _defaults = {
        'cur_rate': 1,
    }

    
    def printed(self,cr,uid,ids,context=None):
        return 'Printing'
    
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

class account_invoice_line(osv.osv):
    _inherit = 'account.invoice.line'
    
    def _product_margin(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = 0
            if line.product_id:
#                if line.product_id.purchase_price:
#                   res[line.id] = round((line.price_unit*line.product_uos_qty*(100.0-line.discount)/100.0) -(line.product_id.purchase_price*line.product_uos_qty), 2)
#                else:
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
                print line.margin
                print line.price_unit*line.quantity*(100.0-line.discount)/100.0
                res[line.id] = (round(line.margin/max(0.01,(line.price_unit*line.quantity*(100.0-line.discount)/100.0)), 2))*100
        return res
        
        
    _columns ={
        'th_weight':fields.float('M. Linere'),
        'margin': fields.function(_product_margin, method=True, string='Marge',store=True),
        'margin_perc': fields.function(_product_margin_perc, method=True, string='% Mar',store=True),
        'location':fields.many2one('stock.location','Emplacement'),

    }
 #   _sql_constraints = [ ('name', 'UNIQUE (name)', 'The name of the partner must be unique !')] 
account_invoice_line()

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
    
    _columns = {
        'instrument_number':fields.char('Instrument', size=64),
    }
account_move_line()


class res_users(osv.osv):
    _inherit = 'res.users'
    _columns = {
        'location':fields.many2one('stock.location','Emplacement'),
        'shop':fields.many2one('sale.shop','Souche'),
    }
res_users()
