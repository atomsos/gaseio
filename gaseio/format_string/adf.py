"""
format_string
"""

import re
import math
# import copy

from collections import OrderedDict
import atomtools.unit
from .. import ext_types
from .. import ext_methods

def remove_head_numbers(data):
    p1 = r'^\s*\d+\.?'
    p2 = r'\n\s*\d+\.?'
    data = re.sub(p1, '', data)
    data = re.sub(p2, '\n', data)
    return data

RE_GEOMETRY = re.compile('GEOMETRY\s*\n([\s\S]+?)\n\s*END', flags=re.IGNORECASE)

ADF_FORMAT_STRING = {
    'calculator': 'ADF',
    # 'ignorance' : r'\s*！.*\n',
    'ignorance': ('!',),
    'primitive_data': OrderedDict({
        r'adf\s+-n\s+(\d+)\s*<<': {
            'important': False,
            'selection': 0,
            'type': float,
            'key': 'calc_arrays/max_core',
        },
        re.compile('DEFINE\s*\n([\s\S]*?)\n\s*END', flags=re.IGNORECASE): {
            # 'debug' : True,
            'important': False,
            'selection': 0,
            'key': 'defines',
            'process': lambda data, arrays: ext_methods.process_defines(data),
        },
        re.compile('ATOMS.*\n(\s*\d*\.?\s*(A[cglmrstu]|B[aehikr]?|C[adeflmnorsu]?|D[bsy]|E[rsu]|F[elmr]?|G[ade]|H[efgos]?|I[nr]?|Kr?|L[airuv]|M[dgnot]|N[abdeiop]?|Os?|P[abdmortu]?|R[abefghnu]|S[bcegimnr]?|T[abcehilm]|U(u[opst])?|V|W|Xe|Yb?|Z[nr])\s+[\s\S]*?)\n\s*END', flags=re.IGNORECASE): {
            # 'debug' : True,
            'prerequisite': ['defines'],
            'important': True,
            'selection': 0,
            'process': lambda data, arrays: ext_methods.datablock_to_numpy(\
                ext_methods.substitute_with_define(\
                    remove_head_numbers(data[0]), arrays.get('defines', None)\
                )),
            'key': [
                {
                    'key': 'symbols',
                    'type': str,
                    'index': ':,0',
                    'process': lambda data, arrays: ext_types.ExtList(data.tolist()),
                },
                {
                    'key': 'positions',
                    'type': float,
                    'index': ':,1:4',
                },
            ],
        },
        re.compile('CHARGE\s+(-?\d+)', flags=re.IGNORECASE): {
            'important': False,
            'selection': 0,
            'type': int,
            'key': 'charge'
        },
        RE_GEOMETRY: {
            'important': False,
            'selection': 0,
            'key': 'calc_arrays/geometry',
        },
        re.compile('SCF\s*\n([\s\S]*?)\n\s*END', flags=re.IGNORECASE): {
            'important': False,
            'selection': 0,
            # 'type' :ext_types.ExtDict,
            'key': 'calc_arrays/scf',
        },
        re.compile('XC\s*\n([\s\S]*?)\n\s*END', flags=re.IGNORECASE): {
            'important': False,
            'selection': 0,
            # 'type' :ext_types.ExtDict,
            'key': 'calc_arrays/xc',
        },
        re.compile('BASIS\s*\n([\s\S]*?)\n\s*END', flags=re.IGNORECASE): {
            'important': False,
            'selection': 0,
            # 'type' :ext_types.ExtDict,
            'key': 'calc_arrays/basis',
        },
        re.compile('BECKEGRID\s*\n([\s\S]*?)\n\s*END', flags=re.IGNORECASE): {
            'important': False,
            'selection': 0,
            # 'type' :ext_types.ExtDict,
            'key': 'calc_arrays/beckegrid',
        },
        re.compile('RELATIVISTIC\s*(.*?)\s*\n', flags=re.IGNORECASE): {
            'important': False,
            'selection': 0,
            'type': str,
            'key': 'calc_arrays/relativistic',
        },
        re.compile('AnalyticalFreq\s*\n([\s\S]*?)\n\s*END', flags=re.IGNORECASE): {
            'important': False,
            'selection': 0,
            # 'type' :ext_types.ExtDict,
            'key': 'calc_arrays/freq',
        },
        re.compile('TITLE\s*([\s\S]*?)\s*\n', flags=re.IGNORECASE): {
            'important': False,
            'selection': 0,
            'type': str,
            'key': 'comments',
        },
    }),
    'synthesized_data': OrderedDict({
    }),
}


ADF_OUT_FORMAT_STRING = ADF_FORMAT_STRING.copy()
ADF_OUT_FORMAT_STRING['primitive_data'] = ADF_FORMAT_STRING['primitive_data'].copy()
del ADF_OUT_FORMAT_STRING['primitive_data'][RE_GEOMETRY]

ext_methods.update(ADF_OUT_FORMAT_STRING, {
    'primitive_data': OrderedDict({
        r'======  Eigenvectors \(columns\) in BAS representation\n([\s\S]*?)\n\n(?: {10,}=|\n)': {
            # 'debug' : True,
            'important': False,
            'selection': 'all',
            'process': lambda data, arrays: \
            ext_methods.process_blockdata_with_several_lines(data,
                                                             ndim_length_regex=r'row\s*\n([\s\S]*?)(?:\n\n|$)',
                                                             rm_header_regex=r'\n\s*column\s+\d+.*\n\s*row\s*\n',
                                                             index_length=5),
            'key': 'calc_arrays/SPIN_Eigenvectors',
        },
        re.compile('GEOMETRY\s*\n([\s\S]+?)\n\s*END'): {
            'important': False,
            'selection': 0,
            'key': 'calc_arrays/geometry',
        },
        r'Coordinates \(Cartesian\)[\s\S]+?-{50,}\n([\s\S]+?)-{50,}': {
            'important': False,
            'selection': 'all',
            'process': lambda data, arrays: ext_methods.datablock_to_numpy(data),
            'key': [
                # {
                #     'key': 'symbols',
                #     'type': str,
                #     'index': ':,1'
                # },
                {
                    'key': 'all_positions',
                    'type': float,
                    'index': ':,5:8'
                }
            ]
        },
        r' {30,}=== (.*) ===\n+ ======  Eigenvectors \(columns\) in BAS representation': {
            'important': False,
            'selection': 'all',
            'key': 'Orbital_names'
        },
        r'Orbital Energies, all Irreps, both Spins\n ={10,}\n\n(.*)\n -{10,}': {
            'important': -False,
            'selection': -1,
            'process': lambda data, arrays: re.split(r' {2,}', data),
            'key': 'Orbital_Energies_headers'
        },
        r'Orbital Energies, all Irreps, both Spins[\s\S]*?-{10,}\n([\s\S]*?)\n\n': {
            'important': -False,
            'selection': -1,
            'process': lambda data, arrays: ext_methods.datablock_to_numpy(data),
            'key': "Orbital_Energies_data"
        },
        r'Bond Energy\s+(.*?)\s+eV': {
            'important': False,
            'selection': -1,
            'type': float,
            'key': 'calc_arrays/potential_energy'
        }
    }),
    'synthesized_data': OrderedDict({
        'positions': {
            'prerequisite': ['all_positions'],
            'equation': lambda arrays: arrays['all_positions'][-1]
        }
    }),
})


# ADF_LOG_FORMAT_STRING = ADF_OUT_FORMAT_STRING.copy()

ADF_LOG_FORMAT_STRING = {
    'calculator': 'ADF',
    'primitive_data': OrderedDict({
        r'Coordinates in Geometry Cycle.*\n\s+Atom.*\)\n([\s\S]+?)<': {
            'important': True,
            'selection': 'all',
            'process': lambda data, arrays: ext_methods.datablock_to_numpy(data),
            'key': [
                {
                    'key': 'all_positions',
                    'type': float,
                    'index': ':,1:4'
                },
                {
                    # 'debug': True,
                    'key': 'symbols',
                    'type': str,
                    'index': ':,0',
                    'process': lambda data, arrays: ['.'.join(_.split('.')[1:]) for _ in data[0]]
                }
            ]
        },
        r'current energy\s+(-?.*\d)\sHartree': {
            # 'debug': True,
            'important': True,
            'selection': 'all',
            'process': lambda data, arrays: float(data) * atomtools.unit.trans_energy('au', 'eV'),
            'key': 'all_potential_energy',
        }
    }),
    'synthesized_data': OrderedDict({
        'positions': {
            'prerequisite': ['all_positions'],
            'equation': lambda arrays: arrays['all_positions'][-1]
        },
        'potential_energy': {
            'prerequisite': ['calc_arrays/all_potential_energy'],
            'equation': lambda arrays: arrays['calc_arrays/all_potential_energy'][-1]
        }
    }),
}


FORMAT_STRING = {
    'adf': ADF_FORMAT_STRING,
    'adf-out': ADF_OUT_FORMAT_STRING,
    'adf-log': ADF_LOG_FORMAT_STRING,
}
