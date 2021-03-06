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

import tools
from osv import fields,osv

class hr_holidays_report(osv.osv):
    _name = "hr.holidays.report"
    _description = "Leaves Statistics"
    _auto = False
    _rec_name = 'date'
    _columns = {
        'date': fields.date('Date', readonly=True),
        'year': fields.char('Year', size=4, readonly=True),
        'day': fields.char('Day', size=15, readonly=True),
        'month':fields.selection([('01','January'), ('02','February'), ('03','March'), ('04','April'),
            ('05','May'), ('06','June'), ('07','July'), ('08','August'), ('09','September'),
            ('10','October'), ('11','November'), ('12','December')], 'Month',readonly=True),
        'date_from' : fields.date('Start Date', readonly=True),
        'date_to' : fields.date('End Date', readonly=True),
        'number_of_days_temp': fields.float('#Days', readonly=True),
        'employee_id' : fields.many2one('hr.employee', "Employee's Name",readonly=True),
        'user_id':fields.many2one('res.users', 'User', readonly=True),
        'holiday_status_id' : fields.many2one("hr.holidays.status", "Leave Type",readonly=True),
        'department_id':fields.many2one('hr.department','Department',readonly=True),
        'state': fields.selection([('draft', 'Draft'),
                                   ('confirm', 'Waiting Validation'),
                                   ('refuse', 'Refused'),
                                   ('validate', 'Validated'),
                                   ('cancel', 'Cancelled')]
                                   ,'State', readonly=True),
    }
    _order = 'date desc'
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'hr_holidays_report')
        cr.execute("""
            create or replace view hr_holidays_report as (
                 select
                     min(s.id) as id,
                     date_trunc('day',s.create_date) as date,
                     date_trunc('day',s.date_from) as date_from,
                     date_trunc('day',s.date_to) as date_to,
                     sum(s.number_of_days_temp) as number_of_days_temp,
                     s.employee_id,
                     s.user_id as user_id,
                     to_char(s.create_date, 'YYYY') as year,
                     to_char(s.create_date, 'MM') as month,
                     to_char(s.create_date, 'YYYY-MM-DD') as day,
                     s.holiday_status_id,
                     s.department_id,
                     s.state
                     from
                 hr_holidays s
                 where type='remove' and
                 s.employee_id is not null
                 group by
                     s.create_date,s.state,s.date_from,s.date_to,
                     s.employee_id,s.user_id,s.holiday_status_id,
                     s.department_id
            )
        """)
hr_holidays_report()

class hr_holidays_remaining_leaves_user(osv.osv):
    _name = "hr.holidays.remaining.leaves.user"
    _description = "Total holidays by type"
    _auto = False
    _columns = {
        'name': fields.char('Employee',size=64),
        'no_of_leaves': fields.integer('Remaining leaves'),
        'user_id': fields.many2one('res.users','User'),
        'leave_type': fields.char('Leave Type',size=64),

    }
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'hr_holidays_remaining_leaves_user')
        cr.execute("""
            create or replace view hr_holidays_remaining_leaves_user as (
                 select
                    min(hrs.id) as id,
                    rr.name as name,
                    sum(hrs.number_of_days) as no_of_leaves,
                    rr.user_id as user_id,
                    hhs.name as leave_type
                from
                    hr_holidays as hrs, hr_employee as hre,
                    resource_resource as rr,hr_holidays_status as hhs
                where
                    hrs.employee_id = hre.id and
                    hre.resource_id =  rr.id and
                    hhs.id = hrs.holiday_status_id
                group by
                    rr.name,rr.user_id,hhs.name
            )
        """)

hr_holidays_remaining_leaves_user()
