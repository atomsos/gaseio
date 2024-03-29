"""
format_string
"""

import re
from collections import OrderedDict


from .. import ext_types
from .. import ext_methods


FORMAT_STRING = {
    'mol2': {
        'ignorance': ('#',),
        # 'ignorance' : r'\s*#.*\n',
        'primitive_data': {
            r'@<TRIPOS>ATOM([\s\S]*?)[@|$]': {
                'important': True,
                'selection': -1,
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data),
                'key': [
                    {
                        'key': 'symbols',
                        'type': str,
                        'index': ':,5',
                        'process': lambda data, arrays: data.tolist(),
                    },
                    {
                        'key': 'positions',
                        'type': float,
                        'index': ':,2:5',
                    },
                ],
            },
        },
        'synthesized_data': OrderedDict({
        }),
    },
}
