# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (C) P. Christeas, 2009, all rights reserved
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

{
	"name" : "Account Invoice Merge",
	"version" : "0.2",
	"author"  : "P. Christeas" ,
	"website" : "http://openerp.hellug.gr",
        "description"  : """ Merge some draft invoices into one.
	Invoices will have to be of the same kind, to the same partner, and then
	their lines will merge into one. Useful to combine auto-generated invoices.
	 """,
	"depends" : ["base","account"],
	"init_xml" : [],
	"demo_xml" : [],
	"update_xml" : ["invoice_merge.xml"],
	"active": False,
	"installable": True
}
