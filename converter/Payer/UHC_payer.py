from flask import Flask
import xml.etree.ElementTree as ET
from payer_abstract import Payer_Abstract

app = Flask(__name__)
app.config["DEBUG"] = True

class UHC_Payer(Payer_Abstract):

    requestor_entity = ['FA','1P']

    requestor_id = ['24','XX']

    requestor_supp = ['EI', 'ZH']

    service_provider_id = ['72','73','77','DD','DK','DQ','FA','G3','P3','QB','QV','SJ']

    certification_type_code = ['I','S']

    def loopA_umo_entity(self,element_child, insurer):
        element_child.text = 'X3'

    def loopA_umo_id(self,element_child, insurer):
        element_child.text = 'PI'

    def loopB_requester_entity(self,element_child, enterer):
        if enterer == 'Practitioner':
            element_child.text = '1P'
        elif enterer == 'Location':
            element_child.text = 'FA'

    def loopB_requester_id(self,req,enterer):
        for id in enterer['identifier']:
            if 'type' in id:
                if id['type']['coding']['system']['code']['value'] == 'PRN':
                    req['id'] = 'XX'
                    req['value'] = id['value']
                    break
                elif id['type']['coding']['system']['code']['value'] == 'TAX':
                    req['id'] = '24'
                    req['value'] = id['value']
                    break
            else:
                req['id'] = 'XX'
                req['value'] = id['value']
        return req

    def loopC_identifier_code_id(self, element_child, patient):
        element_child.text = 'MI'

    def loopD_identifier_code_id(self, element_child, dependent):
        element_child.text = 'MI'

    def loop2000F_certification_code(self,element_child):
        element_child.text = 'I'

