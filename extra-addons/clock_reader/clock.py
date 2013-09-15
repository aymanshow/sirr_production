# -*- encoding: utf-8 -*-
##############################################################################
#
#    Clock Reader for OpenERP
#    Copyright (C) 2004-2009 Moldeo Interactive CT
#    (<http://www.moldeointeractive.com.ar>). All Rights Reserved
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

from osv import osv, fields
import timeutils as tu
from lib.models import labels as clock_labels
from lib.models import default as clock_default
from lib.models import classes as clock_class
from lib.attendance_creator import AttendanceCreator, \
        MultipleAssignedCardError, NotAssignedCardError
import netsvc
import SOAPpy
import httplib
from xml.dom.minidom import parseString

logger = netsvc.Logger()

_uri_help = """Determines the URI string to connect to the clock. The URI is
determined by each model watch. In the case of F5, for example is:
udp://localhost:8000/"""

def setSome(A, B):
    return A != None and A or B

class clock_reader_clock(osv.osv):
    _name = "clock_reader.clock"
    _description = "Clock"
    _columns = {
        'name' : fields.char("Name", size=64, required=True),
        'uri': fields.char('URI', size=128, required=True, help=_uri_help),
        'model': fields.selection(clock_labels, 'Model', required=True),
        'location_id': fields.many2one('hr.department', 'Location',
                                       select=True, ondelete='set null'),
        'timeout': fields.integer('Timeout (sec)'),
        'create_unknown_employee': fields.boolean('Create Unknown Employeers'),
        'ignore_sign_inout': fields.boolean('Ignore sign in/outs'),
        'complete_attendance': fields.boolean('Autocomplete sign in/out'),
        'clean_at_end': fields.boolean('Clean clock at the end'),
        'tolerance': fields.integer('Tolerance', help='In seconds, distance'
                                    ' bettweeen attendance with same action'
                                    ' understanded as the same attendance.'),
        'active': fields.boolean('Active'),
    }
    _sql_constraints = [
        ('uri', 'UNIQUE (uri)', 'The uri of the clock must be unique' )
    ]
    _order = 'uri asc'

    def load_attendances(self, cr, uid, ids,
             clean_at_end = None,
             complete_attendance = None,
             create_unknown_employee = None,
             ignore_sign_inout = None,
             tolerance = None,
             context=None):
        AC = AttendanceCreator(cr, uid, context=context)
        card_err = {}
        empl_err = {}
        empl_id = {}
        err = []
        c = 0
        emp_obj=self.pool.get('hr.employee')
        empl_ids = emp_obj.search(cr,uid,[])
        empl_ids = emp_obj.browse(cr,uid,empl_ids)
        for empl in empl_ids:
            empl_id[empl.matricule]=empl.matricule
        if ids==None:
            ids = self.search(cr, uid, [])
        #print ids
        #print xxxx
        from datetime import datetime
        import csv
        DEBUGFILE = open('/tmp/clock.%s.csv' % datetime.today(), 'w')
        DEBUGCSV  = csv.writer(DEBUGFILE)

        for clock in self.browse(cr, uid, ids):
            C = clock_class[clock.model](clock.uri, timeout=clock.timeout)
            uri=clock.uri
            uri = uri.replace('/','').split(':')
            assert(len(uri) == 3)
            assert(uri[0] == 'udp')
            server_address = uri[1]
            server_port = int(uri[2])
            template="""<?xml version="1.0" standalone="no"?>
            <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
            <SOAP-ENV:Body>
            <GetAttLog>
            <ArgComKey xsi:type="xsd:integer">0</ArgComKey>
            <Arg>
            <PIN xsi:type="xsd:integer">ALL</PIN>
            </Arg>

            </GetAttLog>
            </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>"""

            headers = {'Content-type':'text/xml', 'SOAPAction':'uri:zksoftware'}
            logger.notifyChannel('server-address', netsvc.LOG_DEBUG,server_address)
            logger.notifyChannel('server-port', netsvc.LOG_DEBUG,server_port)

            connection = httplib.HTTPConnection(server_address, server_port)
            connection.request("POST", "/iWsService", template,headers)
            response = connection.getresponse()
            dom = parseString(response.read())
            logs=[]

    #            if not C.connect():
    #                err.append("Can't connect with clock '%s'." % clock.name)
    #                continue
            for node in dom.getElementsByTagName('Row'):
                logger.notifyChannel('server-port', netsvc.LOG_DEBUG,'Row')
                items={}
                for rows in node.childNodes:
                    for elements in node.childNodes:
                        for value in elements.childNodes:
                            items[elements.nodeName]=value.toxml()
                logs.append(items)
            n=1
            for log in logs:
                n=n+1
                action=log['Status']
                workcode=log['WorkCode']
                method=log['Verified']
                dt=log['DateTime']
                card_id=int(log['PIN'])
                if action==0:
                    action='sign_in'
                else:
                    action='sign_out'
                method='fingerprint'
        #            for n, card_id, method, action, dt in C.attendances():
                DEBUGCSV.writerow((n,card_id, workcode, action, dt))

    #                assert isinstance(dt, tu.datetime)

                    # Verifico que esta tarjeta no me haya traido problemas
                    # previamente.
#                if str(card_id)=='20213':
#                    print log
#                    logger.notifyChannel('clock_reader.clock',netsvc.LOG_INFO,'Employee%s-%s-%s'%(card_id,dt,action))
                if card_id in card_err:
                    logger.notifyChannel('wizard.clock_reader', netsvc.LOG_DEBUG,
                                          '_read_clock: Card %i in the black list.'%card_id)
                    continue

                # Verificar si un empleado usa esa tarjeta
                if not card_id in empl_id:
                    try:
                        empl_id[card_id] = AC.employee_id(card_id)
                    except MultipleAssignedCardError, m:
                        card_err[card_id] = str(m)
                        continue

                    except NotAssignedCardError, m:
                        if setSome(create_unknown_employee,
                                   clock.create_unknown_employee):
                            empl_id[card_id] = AC.create_employee(card_id)
                        else:
                            card_err[card_id] = str(m)
                            continue

                    # Verifico que este empleado no me haya traido problemas
                    # previamente.
                    logger.notifyChannel('wizard.clock_reader', netsvc.LOG_DEBUG,
                                        '_read_clock: Employee %i in the black list.' %
                                                                       empl_id[card_id])
                    continue

                    # Si esta todo bien con el empleado, cargo la asistencia.
                if AC.exists_attendance(empl_id[card_id], dt, action):
                    logger.notifyChannel('clock_reader.clock', netsvc.LOG_DEBUG,
                               'read: Attendance %i:%s:%s(%s) yet loaded.' %
                                    (empl_id[card_id], dt, action, method))
                    continue

                # Ignore action
                if setSome(ignore_sign_inout, clock.ignore_sign_inout):
                    cr.execute("""
                        select A1.name, A1.action
                        from hr_attendance as A1
                            left outer join
                            hr_attendance as A2
                            on A1.employee_id=A2.employee_id AND A1.name < A2.name
                        where A2.name is Null and A1.employee_id = %i
                        """ % empl_id[card_id])
                    action = cr.fetchall()
                    if len(action) == 1:
                        action=action[0]
                        if action=='sign_in':
                            action='sign_out'
                        else:
                            action='sign_in'
                        #action='sign_out'
                    else:
                        action='sign_in'
                print 'Action:',n,'Empl',empl_id[card_id]
                r = AC.create_attendance(empl_id[card_id], dt, action, method,
                                         tolerance=setSome(tolerance,
                                                           clock.tolerance),
                                         complete_attendance=setSome(complete_attendance,
                                                                    clock.complete_attendance),
                                         ignore_signs= setSome(ignore_sign_inout, clock.ignore_sign_inout))

                if r != AttendanceCreator.ERROR:
                    c = c + 1
                else:
                    logger.notifyChannel('clock_reader.clock',
                         netsvc.LOG_INFO,
                         'read: Append employee %s to the black list.' %
                         str(empl_id[card_id]))
                    #empl_err[empl_id[card_id]] = str(m)
        DEBUGFILE.close()

            # Recolección de errores
        cards_err = card_err.keys()
        empls_err = empl_err.keys()

        cards_err.sort()
        empls_err.sort()

        err += map(lambda i: card_err[i], cards_err)
        err += map(lambda i: empl_err[i], empls_err)

        return { 'count': c, 'errors': err }

clock_reader_clock()

class hr_attendance(osv.osv):
    _inherit = "hr.attendance"
    _columns = {
        'method': fields.selection([('manual', 'Manual'),
                                    ('automatic', 'Automatic'),
                                    ('keyboard', 'Keyboard'),
                                    ('fingerprint', 'Fingerprint'),
                                    ('rfid', 'RFid'),
                                    ('facerecognition', 'Face recognition'),],
                                   'Authentication method'),
    }

hr_attendance()

class hr_employee(osv.osv):
    _inherit="hr.employee"
    def create_user(self,cr,uid,ids,context=None):
        clock_obj=self.pool.get('clock_reader.clock')
        employee_obj=self.pool.get('hr.employee')
        employee=employee_obj.browse(cr,uid,ids)[0]
        clocks=clock_obj.search(cr,uid,[])
        clocks=clock_obj.browse(cr,uid,clocks)
        clock_response=[]
        for clock in clocks:
            C = clock_class[clock.model](clock.uri, timeout=clock.timeout)
            uri=clock.uri
            uri = uri.replace('/','').split(':')
            assert(len(uri) == 3)
            assert(uri[0] == 'udp')
            server_address = uri[1]
            server_port = int(uri[2])
            template="""<?xml version="1.0" standalone="no"?>
            <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
            <SOAP-ENV:Body>
            <SetUserInfo>
            <ArgComKey xsi:type="xsd:integer">0</ArgComKey>
            <Arg>
            <PIN xsi:type="xsd:integer">%s</PIN>
            <Name xsi:type="xsd:integer">%s</Name>
            
            </Arg>

            </SetUserInfo>
            </SOAP-ENV:Body>
            </SOAP-ENV:Envelope>"""%(employee.matricule,employee.name[:24])

            headers = {'Content-type':'text/xml', 'SOAPAction':'uri:zksoftware'}
            logger.notifyChannel('server-address', netsvc.LOG_DEBUG,server_address)
            logger.notifyChannel('server-port', netsvc.LOG_DEBUG,server_port)

            connection = httplib.HTTPConnection(server_address, server_port)
            connection.request("POST", "/iWsService", template,headers)
            response = connection.getresponse()
            dom=parseString(response.read())
            response=dom.getElementsByTagName('Information')[0].childNodes[0].nodeValue
            if response=='Successfully!':
                response={'clock':clock.name,'state':'Reussi'}
            else:
                response={'clock':clock.name,'state':'Reussi'}
            clock_response.append(response)
        line=''
        for response in clock_response:
                line+=response['clock']+':'+response['state']+'\n'

        raise osv.except_osv('Creation Sur Machine',line)
        return True 
hr_employee()