"""
gase interface to gaseio
"""

import numpy as np
import chemdata
from .ext_types import ExtList

def reg_customized_symbols(arrays):
    if 'customized_symbols' in arrays:
        arrays['symbols'] = [symbol[:2] if symbol[:2] in chemdata.chemical_symbols else symbol[:1]\
                             for symbol in arrays['customized_symbols'] ]


def reg_numbers_symbols(arrays):
    if 'numbers' in arrays:
        arrays['symbols'] = [chemdata.get_element(_) for _ in arrays['numbers']]
    else:
        assert 'symbols' in arrays, 'either numbers or symbols should be in the arrays'
        arrays['numbers'] = np.array([chemdata.get_element_number(_) for _ in arrays['symbols']])
    arrays['symbols'] = ExtList(arrays['symbols'])
    arrays['numbers'] = ExtList(arrays['numbers'])

def reg_charge(arrays):
    if not 'charge' in arrays:
        arrays['charge'] = 0


def reg_spin(arrays):
    if 'multiplicity' in arrays:
        arrays['spin'] = int(arrays['multiplicity']) - 1
    if not 'spin' in arrays: # auto min spin
        arrays['spin'] = int(sum((arrays['numbers']) - arrays['charge'])) % 2


def reg_comments(arrays):
    if not 'comments' in arrays:
        arrays['comments'] = 'Generated by GASEIO'
    elif isinstance(arrays['comments'], list):
        arrays['comments'] = ' '.join(arrays['comments'])
    
reg_functions = [
    reg_customized_symbols,
    reg_numbers_symbols,
    reg_charge,
    reg_spin,
    reg_comments,
]



def regularize_arrays(arrays):
    if isinstance(arrays, list):
        for arr in arrays:
            regularize_arrays(arr)
        return
    for func in reg_functions:
        func(arrays)
