"""
format_string
"""
from collections import OrderedDict
from .. import ext_types
from .. import ext_methods

import re
import math


def remove_head_numbers(data):
    p1 = r'^\s*\d+\.?'
    p2 = r'\n\s*\d+\.?'
    data = re.sub(p1, '', data)
    data = re.sub(p2, '\n', data)
    return data


FORMAT_STRING = {
    'adf' : {
        'calculator': 'ADF',
        'ignorance': ('!',),
        'primitive_data'  : {
            r'adf\s+-n\s+(\d+)\s*<<' : {
                'important' : False,
                'selection' : -1,
                'type' : float,
                'key' : 'maxcore',
                },
            re.compile('DEFINE\s*\n([\s\S]*?)\n\s*END', flags=re.IGNORECASE) : {
                # 'debug' : True,
                'important' : False,
                'selection' : 0,
                'key' : 'defines',
                'process' : lambda data, arrays: ext_methods.process_defines(data),
                },
            re.compile('ATOMS.*\n(\s*\d*\.?\s*(A[cglmrstu]|B[aehikr]?|C[adeflmnorsu]?|D[bsy]|E[rsu]|F[elmr]?|G[ade]|H[efgos]?|I[nr]?|Kr?|L[airuv]|M[dgnot]|N[abdeiop]?|Os?|P[abdmortu]?|R[abefghnu]|S[bcegimnr]?|T[abcehilm]|U(u[opst])?|V|W|Xe|Yb?|Z[nr])\s+[\s\S]*?)\n\s*END', flags=re.IGNORECASE) : {
                # 'debug' : True,
                'important' : True,
                'selection' : 0,
                'process' : lambda data, arrays: ext_methods.datablock_to_numpy(\
                                                 ext_methods.substitute_with_define(\
                                                 remove_head_numbers(data[0]), arrays.get('defines', None)\
                                                 )),
                'key' : [
                    {
                        'key' : 'symbols',
                        'type' : str,
                        'index' : ':,0',
                        'process' : lambda data, arrays: ext_types.ExtList(data.tolist()),
                    },
                    {
                        'key' : 'positions',
                        'type' : float,
                        'index' : ':,1:4',
                    },
                    ],
                },
            re.compile('CHARGE\s+(-?\d+)', flags=re.IGNORECASE) : {
                'important' : False,
                'selection' : -1,
                'type' : int,
                'key' : 'charge'
            },
            re.compile('GEOMETRY\s*\n([\s\S]*?)\n\s*END', flags=re.IGNORECASE) : {
                'important': False,
                'selection' : -1,
                # 'type' :ext_types.ExtDict,
                'key' : 'calc_arrays/geometry',
            },
            re.compile('SCF\s*\n([\s\S]*?)\n\s*END', flags=re.IGNORECASE) : {
                'important': False,
                'selection' : -1,
                # 'type' :ext_types.ExtDict,
                'key' : 'calc_arrays/scf',
            },
            re.compile('XC\s*\n([\s\S]*?)\n\s*END', flags=re.IGNORECASE) : {
                'important': False,
                'selection' : -1,
                # 'type' :ext_types.ExtDict,
                'key' : 'calc_arrays/xc',
                },
            re.compile('BASIS\s*\n([\s\S]*?)\n\s*END', flags=re.IGNORECASE) : {
                'important': False,
                'selection' : -1,
                # 'type' :ext_types.ExtDict,
                'key' : 'calc_arrays/basis',
                },
            re.compile('BECKEGRID\s*\n([\s\S]*?)\n\s*END', flags=re.IGNORECASE) : {
                'important': False,
                'selection' : -1,
                # 'type' :ext_types.ExtDict,
                'key' : 'calc_arrays/beckegrid',
                },
            re.compile('RELATIVISTIC\s*([\s\S]*?)\s*\n', flags=re.IGNORECASE) : {
                'important': False,
                'selection' : -1,
                'type' :str,
                'key' : 'calc_arrays/relativistic',
                },
            re.compile('AnalyticalFreq\s*\n([\s\S]*?)\n\s*END', flags=re.IGNORECASE) : {
                'important': False,
                'selection' : -1,
                # 'type' :ext_types.ExtDict,
                'key' : 'calc_arrays/freq',
                },
            re.compile('TITLE\s*([\s\S]*?)\s*\n', flags=re.IGNORECASE) : {
                'important': False,
                'selection' : -1,
                'type' :str,
                'key' : 'comments',
                },
            },
        'synthesized_data' : OrderedDict({
            }),
    },
}
