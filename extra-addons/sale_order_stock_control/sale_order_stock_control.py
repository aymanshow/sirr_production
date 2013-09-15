##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    
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
from osv import fields, osv
from tools.misc import debug
from tools.translate import _
class sale_order_line(osv.osv):
    _name= "sale.order.line"
    _inherit = "sale.order.line"
    _columns = {
        'stock_ok':fields.boolean('Stock ok?', required=False),
    }
    
    _defaults = {
        'stock_ok': lambda *a: True,
    }

sale_order_line()

class sale_order(osv.osv):
    _name= "sale.order"
    _inherit = "sale.order"    
    
    def _check_global_status(self, cr, uid, ids, field_name, args, context=None):
        if context is None:
            context={}
        result = {}
        for order in self.browse(cr,uid,ids, context=context):
            result[order.id] = True
            if order.order_line != []:
                for line in order.order_line:
                    if line.stock_ok == False:
                        result[order.id] = False
        return result

    _columns = {
        'global_status': fields.boolean('Global Status'),
    }
    
    _defaults = {
        'global_status': lambda *a: True,
    }    
    
    def check_order_validity(self, cr, uid, ids, context=None):
        """
        This method check if all order lines have enough virtual stock.
    
        @param cr: cursor to database
        @param user: id of current user
        @param ids: list of record ids to be process
        @param context: context arguments, like lang, time zone
        
        @return: return a result
        """
        if context is None:
            context={}
        global_state=True
        for order in self.browse(cr,uid,ids, context=context):
            overstock_lines = self.check_stock(cr, uid, ids, context)    
            self.check_emptyness(cr, uid, ids, context)
            self.check_stock(cr, uid, ids, context)
        res={}
        for order in self.browse(cr,uid,ids):
            for line in order.order_line:
                if line.stock_ok==False:
                    global_state=False 
                    self.pool.get('sale.order').write(cr,uid,[order.id],{'global_status':False})
                    return False	
        self.write(cr,uid,[order.id],{'global_status':True})
        return global_state
    
    def check_stock(self, cr, uid, ids, context=None):
        order = self.browse(cr,uid,ids, context=context)[0]
        shop_id = order.shop_id.id
        order_line_ids = order.order_line
        product_pool = self.pool.get('product.product')
        location_pool = self.pool.get('stock.location')
        order_line_pool = self.pool.get('sale.order.line')
        overstock_lines = []
        
        for order_line in order_line_ids:
            location=order_line.location
            context['location'] = location.id
            product = product_pool.browse(cr,uid,order_line.product_id.id, context=context)
            if product.type=='service':
                order_line.write({'stock_ok':True})
            #elif product.procure_method=='make_to_order':
            #    order_line.write({'stock_ok':True})
            else:            
            	if int(order_line.product_uom_qty) > int(product.virtual_available):
                	order_line.write({'stock_ok' : False})
                	overstock_lines.append(order_line.name)
            	else:
                	order_line.write({'stock_ok' : True})
        return overstock_lines
            
            
    
    def check_emptyness(self, cr, uid, ids, context=None):
        if context is None:
            context={}
        if self.browse(cr,uid,ids, context=context)[0].order_line == []:
            raise osv.except_osv(_('Warning'), _('Aucune ligne de commande retrouvee!'))    
        return True        
    
sale_order()