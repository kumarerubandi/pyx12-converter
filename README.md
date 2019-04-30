# Pyx12

[![Build Status](https://travis-ci.org/azoner/pyx12.png?branch=master)](https://travis-ci.org/azoner/pyx12)
<!-- [![Coverage Status](https://coveralls.io/repos/azoner/pyx12/badge.png?branch=master)](https://coveralls.io/r/azoner/pyx12?branch=master) -->

Pyx12 is a HIPAA X12 document validator and converter.  It parses an ANSI X12N data file and validates it against a representation of the Implementation Guidelines for a HIPAA transaction.  By default, it creates a 997 response for 4010 and a 999 response for 5010. It can create an html representation of the X12 document or can translate to and from an XML representation of the data file. 

# Installation


    1.Clone the repository 
        git clone https://github.com/hajiratasneem/pyx12-converter
    2.In a terminal, navigate to the directory the project is clone into.
    3.Run python setup.py install
    4.Navigate to converter/Payer
    5.Run python payer_common.py
