from flask import Flask, render_template, redirect, url_for,request
from abc import ABCMeta, abstractmethod
import json
import xml.etree.ElementTree as ET

app = Flask(__name__)
app.config["DEBUG"] = True

class Payer_Abstract():
    __metaclass__ = ABCMeta

    @abstractmethod
    def loopA_umo_entity(self, loop_elem, claim_json):
        pass

    @abstractmethod
    def loopA_umo_id(self, loop_elem, claim_json):
        pass

    @abstractmethod
    def loopA_umo_id_value(self, loop_elem, claim_json):
        pass

    @abstractmethod
    def loopB_requester_entity(self,element_child, enterer):
        pass

    @abstractmethod
    def loopB_requester_id(self,req,enterer):
        pass

    @abstractmethod
    def loopC_identifier_code_id(self, loop_elem, claim_json):
        pass

    @abstractmethod
    def loopD_identifier_code_id(self, loop_elem, claim_json):
        pass

    @abstractmethod
    def loop2000F_certification_code(self, element_child):
        pass