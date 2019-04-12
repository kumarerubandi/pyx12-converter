from flask import Flask, render_template, redirect, url_for,request
import json
import xml.etree.ElementTree as ET
from UHC_payer import UHC_Payer
from converter_method import Converter
from flask_cors import CORS

app = Flask(__name__)
app.config["DEBUG"] = True
CORS(app)

payer = UHC_Payer()
converter = Converter()

umo_code = ['X3','2B','36','PR']

umo_id = ['24','34','46','PI','XV']

requestor_entity = ['FA','1P','2B','36','PR']

requestor_id = ['24','34','46','XV','XX']

requestor_supp = ['EI', 'ZH']

certification_type_code = ['1','2','3','4','I','N','R','S']

service_provider_id = ['72','73','77','DD','DK','DQ','FA','G3','P3','QB','QV','SJ']

identification_code = ['MI','II']

@app.route('/x12fhir', methods=['POST','GET'])
def convertToFhir():
    return "fhir"

def get_json():
    with open("/var/www/html/claim.json", 'r') as file_object:
        return file_object.read()

@app.route('/xmlx12', methods=['POST','GET'])
def convertToX12():
    req_json = json.loads(request.data)
    if 'claim_json' in req_json:
        claim_json = req_json['claim_json']

    standard_278 = ET.parse("standard_278.xml")
    # claim_json = json.loads(get_json())
    pa_xml = standard_278.getroot()
    loop_elems = [element for element in pa_xml.getiterator() if element.tag=='loop']
    st_elem = [element for element in pa_xml.getiterator() if
                    element.tag == 'loop' and element.attrib['id'] == 'DETAIL']

    for loop_elem in loop_elems[:]:
        # UMO
        if loop_elem.attrib['id'] == '2010A':
            if 'insurer' in claim_json:
                loopA(loop_elem, claim_json)
            else:
                st_elem[0].remove(loop_elem)
        # Requestor Name
        elif loop_elem.attrib['id'] == '2010B':
            if 'enterer' in claim_json:
                loopB(loop_elem,claim_json)
            else:
                st_elem[0].remove(loop_elem)
        # Subscriber Name
        elif loop_elem.attrib['id'] == '2010C':
            if 'patient' in claim_json:
                loopC(loop_elem, claim_json)
            else:
                st_elem[0].remove(loop_elem)
        #Dependent Name
        elif loop_elem.attrib['id'] == '2010D':
            if 'payee' in claim_json:
                loopD(loop_elem, claim_json)
            else:
                st_elem[0].remove(loop_elem)
        elif loop_elem.attrib['id'] == '2000E':
            if 'procedure' in claim_json:
                loopE(loop_elem, claim_json)
            else:
                st_elem[0].remove(loop_elem)
        elif loop_elem.attrib['id'] == '2010EA':
            if 'provider' in claim_json:
                loopEA(loop_elem, claim_json)
            else:
                st_elem[0].remove(loop_elem)
                # print "loop EA---------",ET.tostring(loop_elem)
        elif loop_elem.attrib['id'] == '2000F':
            if 'procedure' in claim_json:
                procedure_codes = []
                procedure_desc = []
                for p in claim_json['procedure']:
                    if 'procedureCodeableConcept' in p:
                        if 'coding' in p['procedureCodeableConcept']:
                            procedure_codes.append(p['procedureCodeableConcept']['coding'][0]['code'])
                        else:
                            procedure_desc.append(p['procedureCodeableConcept']['text'])
                loop2000F(loop_elem, claim_json,procedure_codes, procedure_desc)

            else:
                st_elem[0].remove(loop_elem)
        # Service Provider
        elif loop_elem.attrib['id'] == '2010F':
            if 'careTeam' in claim_json:
                loop2010F( claim_json, pa_xml)
            else:
                st_elem[0].remove(loop_elem)
    # print "final----------", ET.tostring(pa_xml)
    output_x12 = converter.convertXMLToX12(ET.tostring(pa_xml))
    print "-----"
    print output_x12
    print "---------",str(output_x12.replace ('~', '~\n'))
    return json.dumps({"x12_response":str(output_x12.replace ('~', '~\n'))})

def loopA(loop_elem, claim_json):
    insurer = {}
    seg_children = loop_elem.getchildren()
    if 'contained' in claim_json:
        for c in claim_json['contained']:
            if 'id' in c:
                if c['id'] == claim_json['insurer']['reference'][1:]:
                    insurer = c
                    break
    if insurer:
        for seg_child in seg_children[:]:
            if seg_child.attrib['id'] == 'NM1':
                element_children = seg_child.getchildren()
                for element_child in element_children[:]:
                    if element_child.attrib['id'] == 'NM101':
                        payer.loopA_umo_entity(element_child, insurer['resourceType'])
                    if element_child.attrib['id'] == 'NM108':
                        payer.loopA_umo_id(element_child, insurer['resourceType'])

        modify_name(loop_elem,insurer)

def loopB(loop_elem,claim_json):
    req = {'id': '', 'value': ''}
    enterer = {}
    seg_children = loop_elem.getchildren()
    for c in claim_json['contained']:
        # print " before element_child.text.....", element_child.text, element_child.tag
        if 'resourceType' in c:
            if 'id' in c:
                if c['id'] == claim_json['enterer']['reference'][1:]:
                    enterer = c
    if enterer:
        for seg_child in seg_children[:]:
            if seg_child.attrib['id'] == 'NM1':
                element_children = seg_child.getchildren()
                for element_child in element_children[:]:
                    # print "child.attrib['id']", element_child.attrib['id']
                    if element_child.attrib['id'] == 'NM101':
                        # print "UMO------", element_child.tag, element_child.text
                        payer.loopB_requester_entity(element_child, enterer['resourceType'])

                        if enterer['resourceType']== 'Location':
                            if element_child.attrib['id'] == 'NM104':
                                # print "seg child",element_child.attrib
                                seg_child.remove(element_child)
                            if element_child.attrib['id'] == 'NM103':
                                element_child.text = enterer['name']
                        elif enterer['resourceType']== 'Practitioner':
                            modify_name(seg_child, enterer)
                    if 'identifier' in enterer:
                        req_id = payer.loopB_requester_id(req,enterer)
                        if element_child.attrib['id'] == 'NM108':
                            element_child.text = req_id['id']
                        if element_child.attrib['id'] == 'NM109':
                            element_child.text = req_id['value']
            # elif seg_child.attrib['id'] == 'REF':
            #     element_children = seg_child.getchildren()
            #     for element_child in element_children[:]:
            #         if element_child.attrib['id'] == 'REF01':
            #             if req['id'] == '24':
            #                 element_child.text = requestor_supp[0]
            #             elif req['id'] == 'XX':
            #                 element_child.text = requestor_supp[1]
            #         if element_child.attrib['id'] == 'REF02':
            #             element_child.text = req['value']
            elif seg_child.attrib['id'] == 'N3':
                if 'address' in enterer:
                    if 'text' in enterer['address'][0]:
                        modify_name(seg_child, enterer)
                    else:
                        loop_elem.remove(seg_child)
                else:
                    loop_elem.remove(seg_child)
            elif seg_child.attrib['id'] == 'N4':
                if 'address' in enterer:
                    modify_name(seg_child, enterer)
                else:
                    loop_elem.remove(seg_child)
            elif seg_child.attrib['id'] == 'PER':
                phone_segment(loop_elem, enterer, seg_child)

def loopC(loop_elem, claim_json):
    seg_children = loop_elem.getchildren()
    patient = {}
    if 'contained' in claim_json:
        # print "claim--------",claim_json
        # print "---------",type(claim_json['contained'])
        for c in claim_json['contained']:
            if 'id' in c:
                if c['id'] == claim_json['patient']['reference'][1:]:
                    patient = c
                    break
    if patient:
        for seg_child in seg_children[:]:
            if seg_child.attrib['id'] == 'NM1':
                element_children = seg_child.getchildren()
                for element_child in element_children[:]:
                    if element_child.attrib['id'] == 'NM108':
                        payer.loopC_identifier_code_id(element_child, patient['resourceType'])
            elif seg_child.attrib['id'] == 'PER':
                phone_segment(loop_elem, patient, seg_child)
        modify_name(loop_elem,patient)

def loopD(loop_elem, claim_json):
    dependent = {}
    for c in claim_json['contained']:
        if 'resourceType' in c:
            if 'id' in c:
                if c['id'] == claim_json['payee']['party']['reference'][1:]:
                    if c['resourceType'] == 'RelatedPerson':
                        dependent = c
    if dependent:
        seg_children = loop_elem.getchildren()
        for seg_child in seg_children[:]:
            if seg_child.attrib['id'] == 'NM1':
                element_children = seg_child.getchildren()
                for element_child in element_children[:]:
                    if element_child.attrib['id'] == 'NM108':
                        payer.loopD_identifier_code_id(element_child, dependent['resourceType'])
                    # element_child.text = "MI"
            elif seg_child.attrib['id'] == 'PER':
                phone_segment(loop_elem,dependent,seg_child)
        modify_name(loop_elem, dependent)


def loopE(loop_elem, claim_json):
    seg_children = loop_elem.getchildren()
    if 'procedure' in claim_json:
        procedure = claim_json['procedure']
    if 'diagnosis' in claim_json:
        diagnosis = claim_json['diagnosis']
    for seg_child in seg_children[:]:
        if seg_child.attrib['id'] == 'UM':
            element_children = seg_child.getchildren()
            for element_child in element_children[:]:
                if element_child.attrib['id'] == 'UM03':
                    if 'code' in claim_json['healthCareService']:
                        element_child.text = claim_json['healthCareService']['code']
                    else:
                        seg_child.remove(element_child)
        elif seg_child.attrib['id'] == 'HI':
            element_children = seg_child.getchildren()
            for element_child in element_children[:]:
                if element_child.attrib['id'] == 'HI':
                    # if 'diagnosis' in claim_json:
                    #     print "len(claim_json['diagnosis'])",len(claim_json['diagnosis'])
                    #     if len(claim_json['diagnosis'])>0:
                    modify_conditions(claim_json['diagnosis'], element_child)
                    #     else:
                    #         print "in...."
                    #         seg_child.remove(element_child)
                    # else:
                    #     seg_child.remove(element_child)
                    # dom = xml.dom.minidom(element_child)
                    # pretty_xml_as_string = dom.toprettyxml()
                    # sub_element_children =element_child.getchildren()
                    # for  sub_element_child in sub_element_children[:]:
                    #     if 'diagnosis' in claim_json:
                    #         print 'inside loop e'
                    # modify_conditions(claim_json['diagnosis'],sub_element_child)
                    # if sub_element_child.attrib['id'] == 'HI01-02':
                    #     sub_element_child.text = diagnosis[0]['diagnosisCodeableConcept']['coding'][0]['code']
                    # elif sub_element_child.attrib['id'] == 'HI01-04':
                    #     sub_element_child.text =  diagnosis[0]['onsetDateTime']
                    # if procedure:
                    #     modify_name(loop_elem,procedure)


def loopEA(loop_elem, claim_json):
    provider = {}
    if 'contained' in claim_json:
        for c in claim_json['contained']:
            if 'id' in c:
                if c['id'] == claim_json['provider']['reference'][1:]:
                    provider = c
                    break
    if provider:
        seg_children = loop_elem.getchildren()
        for seg_child in seg_children[:]:
            if seg_child.attrib['id'] == 'PER':
                phone_segment(loop_elem, provider, seg_child)
        modify_name(loop_elem, provider)


def loop2000F(loop_elem, claim_json,procedure_codes, procedure_desc):
    claim_type = ""
    # print "procedure codes-------",procedure_codes, len(procedure_codes)
    if "type" in claim_json:
        if "coding" in claim_json['type']:
            claim_type = claim_json['type']['coding'][0]['code']
    seg_children = loop_elem.getchildren()
    for seg_child in seg_children[:]:
        if seg_child.attrib['id'] == 'UM':
            element_children = seg_child.getchildren()
            for element_child in element_children[:]:
                if element_child.attrib['id'] == 'UM02':
                    payer.loop2000F_certification_code(element_child)
                if element_child.attrib['id'] == 'UM03' and 'healthCareService' in claim_json:
                    if 'code' in claim_json['healthCareService']:
                        element_child.text = claim_json['healthCareService']['code']
        if claim_type == 'institutional':
            # print "sv2---", claim_type,seg_child.attrib['id']
            if seg_child.attrib['id'] == 'SV2':
                element_children = seg_child.getchildren()
                for element_child in element_children[:]:
                    if element_child.attrib['id'] == 'SV201-02':
                        if len(procedure_codes) == 1:
                            element_child.text = procedure_codes[0]
                        else:
                            seg_child.remove(element_child)
                            add_procedures_institutional(procedure_codes, seg_child)
                    elif element_child.attrib['id'] == 'SV201-07':
                        if len(procedure_desc) > 0:
                            element_child.text = procedure_desc[0]
                        else:
                            seg_child.remove(element_child)

            if seg_child.attrib['id'] == 'SV1':
                loop_elem.remove(seg_child)
        elif claim_type == 'professional':
            if seg_child.attrib['id'] == 'SV1':
                element_children = seg_child.getchildren()
                for element_child in element_children[:]:
                    if element_child.attrib['id'] == 'SV101-02':
                        if len(procedure_codes) == 1:
                            element_child.text = procedure_codes[0]
                        else:
                            seg_child.remove(element_child)
                            add_procedures_professional(procedure_codes,seg_child)
                    elif element_child.attrib['id'] == 'SV101-07':
                        if len(procedure_desc)>0:
                            element_child.text = procedure_desc[0]
                        else:
                            seg_child.remove(element_child)
            if seg_child.attrib['id'] == 'SV2':
                loop_elem.remove(seg_child)



def loop2010F(claim_json, pa_xml):
    providers = []
    loop_2010F ="""<loop id="2010F" repeat="0">
                <seg id="NM1">
                  <ele id="NM101">P3</ele>
                  <ele id="NM103">claim_json.provider.name.0.family</ele>
                  <ele id="NM104">claim_json.provider.name.0.given.0</ele>
                  <!--<ele id="NM106">claim_json.provider.name.0.prefix</ele>-->
                  <!--<ele id="NM107">claim_json.provider.name.0.suffix</ele>-->
                  <ele id="NM108">XX</ele>
                  <ele id="NM109">claim_json.provider.identifier.0.value</ele>
               </seg>
               <!--<seg id="REF">-->
                  <!--<ele id="REF01">EI</ele>-->
                  <!--<ele id="REF02">Service Provider Supplemental Identifier</ele>-->
               <!--</seg>-->
               <seg id="N4">
                  <ele id="N401">claim_json.provider.address.0.city</ele>
                  <ele id="N402">claim_json.provider.address.0.state</ele>
                  <ele id="N403">claim_json.provider.address.0.postalCode</ele>
                  <!--Country Subdivision Code-->
                  <!--<ele id='N407'>claim_json.careTeam.provider.address</ele>-->
               </seg>
               <!--Service Provider contact information-->
               <seg id='PER'>
                   <ele id='PER03'>TE</ele>
                   <ele id='PER04'>claim_json.provider.telecom.0.value</ele>
               </seg>
               <!--Reference Identification Qualifier-->
               <!--<seg id='PRV'>-->
               <!--<ele id='PRV02'>PXC</ele>-->
               <!--<ele id='PRV03'>101Y00000X</ele>-->
               <!--</seg>-->
           </loop>"""
    st_loop_elem = [element for element in pa_xml.getiterator() if
                    element.tag == 'loop' and element.attrib['id'] == 'DETAIL']
    if 'contained' in claim_json:
        for c in claim_json['contained']:
            for p in claim_json['careTeam']:
                if 'id' in c:
                    if c['id'] == p['provider']['reference'][1:]:
                        providers.append(c)
    final_array = []
    z = 0
    for p in providers:
        if z < 3:
            final_array.append(ET.fromstring(loop_2010F))
            z = z + 1
    j = 0
    while j < len(final_array):
        modify_name(final_array[j], providers[j])
        j = j + 1
    for a in final_array:
        st_loop_elem[0].append(a)

    provider_elems = [element for element in st_loop_elem[0].getiterator() if
                          element.tag == 'loop' and element.attrib['id'] == '2010F']
    for p in provider_elems:
        if len(p.getchildren())==0:
            st_loop_elem[0].remove(p)
            break

def phone_segment(loop_elem,claim_json,seg_child):
    if 'telecom' in claim_json:
        telecom_values = []
        for t in claim_json['telecom']:
            contact_val = {'id': 'TE', 'value': ''}
            # print "t['value']--------", t
            if 'value' in t:
                if 'system' in t:
                    if t['system'] == 'phone':
                        contact_val['id'] = 'TE'
                    elif t['system'] == 'email':
                        contact_val['id'] = 'EM'
                    elif t['system'] == 'fax':
                        contact_val['id'] = 'FX'
                    elif t['system'] == 'url':
                        contact_val['id'] = 'UR'
                    contact_val['value'] = str(t['value'])
                telecom_values.append(contact_val)
        if len(telecom_values) > 0:
            modify_telecom(telecom_values, seg_child)
    else:
        loop_elem.remove(seg_child)

def modify_conditions(condition_values, seg_child):
    i = 0
    a = 0
    b = 1
    c = 2
    d = 3
    z = 0
    while (z < len(condition_values)):
        if i < 9:
            id = str('HI0' + str(int(i + 1)) + '-0' + str(int(a + 1)))
            v = str('HI0' + str(int(i + 1)) + '-0' + str(int(b + 1)))
            dtp = str('HI0' + str(int(i + 1)) + '-0' + str(int(c + 1)))
            dt = str('HI0' + str(int(i + 1)) + '-0' + str(int(d + 1)))
        else:
            id = str('HI' + str(int(i + 1)) + '-0' + str(int(a + 1)))
            v = str('HI' + str(int(i + 1)) + '-0' + str(int(b + 1)))
            dtp = str('HI' + str(int(i + 1)) + '-0' + str(int(c + 1)))
            dt = str('HI' + str(int(i + 1)) + '-0' + str(int(d + 1)))

        iden_elem = ET._Element("subele", {'id': id})
        iden_elem.text = 'ABF'
        seg_child.append(iden_elem)
        # seg_child.append(ET._Element('\n'))
        value_elem = ET._Element("subele", {'id': v})
        value_elem.text = str(condition_values[z]['diagnosisCodeableConcept']['coding'][0]['code'])
        seg_child.append(value_elem)
        # seg_child.append(ET._Element('\n'))
        iden_elem = ET._Element("subele", {'id': dtp})
        iden_elem.text = str('D8')
        seg_child.append(iden_elem)
        value_elem = ET._Element("subele", {'id': dt})
        if 'onsetDateTime' in condition_values[z]:
            date_time = condition_values[z]['onsetDateTime']
            value_elem.text = str(date_time)
            seg_child.append(value_elem)
        else:
            value_elem.text = ''
        z = z + 1
        i = i + 1

def add_procedures_professional(procedures,seg_child):
    procedure_values = []
    for t in procedures:
        procedure_values.append({'id': 'SV101-0', 'value': str(t)})
    i = 1
    z = 0
    # print "procedure values-------", procedure_values
    while (z < len(procedures)) and i<7:
        v = str('SV101-0' + str(int(i + 1)))
        value_elem = ET._Element("ele", {'id': v})
        value_elem.text = str(procedure_values[z]['value'])
        seg_child.append(value_elem)
        z = z + 1
        i = i + 1

def add_procedures_institutional(procedures,seg_child):
    procedure_values = []
    for t in procedures:
        procedure_values.append({'id': 'SV201-0', 'value': str(t)})
    i = 1
    z = 0
    # print "procedure values-------", procedure_values
    while (z < len(procedures)) and i<7:
        v = str('SV201-0' + str(int(i + 1)))
        value_elem = ET._Element("ele", {'id': v})
        value_elem.text = str(procedure_values[z]['value'])
        seg_child.append(value_elem)
        z = z + 1
        i = i + 1

def modify_telecom(telecom_values, seg_child):
    i = 1
    j = 2
    z = 0
    # print "telecom_values", telecom_values
    while (z < len(telecom_values)):
        id = str('PER0' + str(int(i + 2)))
        v = str('PER0' + str(int(j + 2)))
        iden_elem = ET._Element("ele", {'id': id})
        iden_elem.text = str(telecom_values[z]['id'])
        seg_child.append(iden_elem)
        value_elem = ET._Element("ele", {'id': v})
        value_elem.text = str(telecom_values[z]['value'])
        seg_child.append(value_elem)
        z = z + 1
        i = i + 2
        j = j + 2
    # print "sssssssssss",ET.tostring(seg_child)

def modify_name(pa_xml, claim_json):
    claim_values = [element for element in pa_xml.getiterator() if 'claim_json' in element.text]
    # print "claim values-------",claim_values
    for c in claim_values:
        keys = c.text.split('.')
        i = 3
        if keys[i-1] in claim_json:
            final_val = claim_json[keys[i-1]]
            # print "final val-----before-----", final_val
            while i< len(keys):
                try:
                    keys[i] = int(keys[i])
                    final_val = final_val[keys[i]]
                except:
                    keys[i] = str(keys[i])
                    if keys[i] in final_val:
                        final_val = final_val[keys[i]]
                i +=1
            # print "final val-----after---------", final_val
            c.text = final_val
        else:
            parent_map = [p for p in pa_xml.getiterator() for ch in p if ch.text == c.text]
            if parent_map[0].attrib['id'] == 'PER' or parent_map[0].attrib['id'] == 'N3' or parent_map[0].attrib['id'] == 'N4':
                pa_xml.remove(parent_map[0])
            else:
                parent_map[0].remove(c)

app.run()
