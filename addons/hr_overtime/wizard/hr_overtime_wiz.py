from osv import fields, osv
import time
import datetime
import wizard
debtors_list_fields = {
        'code':{'string':'Code Client','type':'char'},
    }

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

class hr_overtime_wiz(wizard.interface):

    def calculate_hs(self,cr,uid,ids,context=None):
        emp_obj=self.pool.get('hr.employee')
        att_obj=self.pool.get('hr.attendance')
        now=datetime.datetime.now()
        days=6
        monday=1
        days=now.isoweekday()+days
        start=str((datetime.datetime.now()-datetime.timedelta(days=days)).date())
        end=str(datetime.datetime.now().date())
        employees=emp_obj.search(cr,uid,[])
        absent_employees=[]
        for employee in employees:
            atts=att_obj.search(cr,uid,[('employee_id','=',employee.id),('day','>=',start),('day','<',end)])
            atts=att_obj.browse(cr,uid,atts)
            dates=[]
            hours=0
            for att in atts:
                if att.day not in days:
                    days.append(att.day)
            for date in dates:
                atts=att_obj.search(cr,uid,[('employee_id','=',employee.id),('day','=',date)])
                atts=att_obj.browse(cr,uid,atts)
                end_time=False
                for att in atts:
                    if len(atts)>1:
                        if end_time:
                            start_time=att.name
                        else:
                            end_time=att.name
                if len(atts)>1:
                    hours+=(end_time-start_time).seconds/(60*60)
            print hours
        return True                                            

    def _get_defaults(self, cr, uid, data, context={}):
        now=datetime.datetime.now()
        return data['form']

    def _get_states(self, cr, uid, data, context):
        return 'print_report_c'

    def _get_records(self, cr, uid, data, context={}):
        inv_obj = pooler.get_pool(cr.dbname).get('account.move.line')

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


hr_overtime_wiz('hr.overtime.wiz')