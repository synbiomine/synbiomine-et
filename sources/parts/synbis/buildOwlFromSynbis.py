#!/usr/bin/env python3

import owlready as owr

onto = owr.Ontology('http://dummy.owl')
print(owr.to_owl(onto))