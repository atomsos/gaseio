"""
format_string contain vasp-out

"""


from collections import OrderedDict
import numpy as np


from .. import ext_methods
from .. import ext_types


def parse_INCAR(data, index):
    return ext_methods.parse_config_content(data, add_header=True)


def format_pseudopotential(arrays, for_each_atom=False):
    # 'equation': lambda arrays: [x for y in [[x]*y for (x, y) in zip(arrays['calc_arrays']['vasp_pot'], arrays['ions_per_type'])] for x in y],
    # import pdb; pdb.set_trace()
    vasp_pot = arrays['calc_arrays']['vasp_pot']
    ions_per_type = arrays['ions_per_type']
    output = []
    for p, i in zip(vasp_pot, ions_per_type):
        functional, symbol, created_date = p.split()
        res = {
            'functional': functional,
            'symbol': symbol,
            'created_date': created_date,
        }
        if for_each_atom:
            for _ in range(i):
                output += [res.copy()]
        else:
            output += [res]
    return output


FORMAT_STRING = {
    'OUTCAR': {
        'file_format': 'plain_text',
        'calculator': 'VASP',
        'primitive_data': OrderedDict({
            r'free  energy   TOTEN\s*=\s*(.*?)\s+eV\s*\n': {
                'important': True,
                'selection': -1,
                'type': float,
                'key': 'calc_arrays/freeE',
            },
            r'energy  without entropy=\s*(.*?)\s+': {
                'important': True,
                'selection': -1,
                'type': float,
                'key': 'calc_arrays/E_without_S',
            },
            r'energy\(sigma->0\)\s*=\s*(.*)': {
                'important': True,
                'selection': -1,
                'type': float,
                'key': 'calc_arrays/potential_energy',
            },
            r'ions per type\s*=\s*(.*)\n': {
                'important': True,
                'selection': -1,
                'type': list,
                'process': lambda data, arrays:
                ext_methods.datablock_to_numpy(data).astype(int).flatten(),
                'key': 'ions_per_type',
            },
            r'VRHFIN\s*=\s*(.*?):': {
                'important': True,
                'selection': 'all',
                'process': lambda data, arrays: data.strip(),
                'type': ext_types.ExtList,
                'key': 'element_types',
            },
            r'POSITION\s*TOTAL-FORCE[\s\S]*?-{2,}\n([\s\S]*?)\n\s+-{2,}': {
                'important': True,
                'selection': 'all',
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data),
                'key': [
                    {
                        'key': 'all_positions',
                        'type': float,
                        'index': ':,:3'
                    },
                    {
                        'key': 'calc_arrays/all_forces',
                        'type': float,
                        'index': ':,3:6'
                    },
                ],
            },
            r'direct lattice vectors                 reciprocal lattice vectors([\s\S]+?)\n\n': {
                # 'debug': True,
                'important': False,
                'selection': -1,
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data),
                'key': [
                    {
                        'key': 'cell',
                        'type': float,
                        'index': ':,:3',
                    },
                    {
                        'key': 'reciprocal',
                        'type': float,
                        'index': ':,3:6',
                    },
                ],
            },
            r'FORCES acting on ions[\s\S]*?-{2,}\n([\s\S]*?)\s+-{2,}': {
                'important': True,
                'selection': 'all',
                'process': lambda data, arrays: {
                    'forces_e_ion': ext_methods.datablock_to_numpy(data)[:, 0:3],
                    'forces_ewald': ext_methods.datablock_to_numpy(data)[:, 3:6],
                    'forces_nonlocal': ext_methods.datablock_to_numpy(data)[:, 6:9],
                    'forces_convergence_correction': ext_methods.datablock_to_numpy(data)[:, 9:12],
                },
                'key': 'calc_arrays/all_forces_acting_on_ions',
            },
            r'POTCAR: *(.*?) *\n *VRHFIN': {
                # 'debug': True,
                'important': True,
                'selection': 'all',
                'process': lambda data, arrays: data.strip(),
                'key': 'calc_arrays/vasp_pot',
                # 'type': ext_types.ExtList,
            },
        }),
        'synthesized_data': OrderedDict({
            'symbols': {
                'prerequisite': ['ions_per_type', 'element_types'],
                'equation': lambda arrays: [x for y in [[x]*y for (x, y) in zip(arrays['element_types'], arrays['ions_per_type'])] for x in y],
                'delete': ['element_types'],
            },
            'positions': {
                'prerequisite': ['all_positions'],
                'equation': lambda arrays: arrays['all_positions'][-1]
            },
            'calc_arrays/pseudopotential': {
                'prerequisite': ['ions_per_type', 'calc_arrays/vasp_pot'],
                # 'equation': lambda arrays: [x for y in [[x]*y for (x, y) in zip(arrays['calc_arrays']['vasp_pot'], arrays['ions_per_type'])] for x in y],
                'equation': lambda arrays: format_pseudopotential(arrays),
                'delete': [
                    # 'vasp_pot',
                    'ions_per_type'
                ],
            },
            'calc_arrays/forces': {
                'prerequisite': ['calc_arrays/all_forces'],
                'equation': lambda arrays: arrays['calc_arrays']['all_forces'][-1]
            },
        }),
    },
    'POSCAR': {
        'calculator': 'VASP',
        'primitive_data': {
            r'^(.*)\n': {
                'important': True,
                'selection': -1,
                'type': str,
                'key': 'comments',
            },
            r'^.*\n(.*)\n': {
                # 'debug' : True,
                'important': True,
                'selection': -1,
                'type': float,
                'key': 'scaling_factor',
            },
            r'^(?:.*\n.*\n)(.*\n.*\n.*\n)': {
                'important': True,
                'selection': -1,
                'prerequisite': ['scaling_factor'],
                'process': lambda data, arrays:
                ext_methods.datablock_to_numpy(
                    data) * arrays['scaling_factor'],
                'key': 'cell',
            },
            r'^(?:.*\n.*\n.*\n.*\n.*\n)(.*)\n': {
                # 'debug' : True,
                'important': True,
                'selection': 0,
                'process': lambda data, arrays: ext_types.ExtList(data.strip().split()),
                'key': 'element_types',
            },
            r'^(?:.*\n.*\n.*\n.*\n.*\n.*\n)(.*)\n': {
                # 'debug' : True,
                'important': True,
                'selection': 0,
                'process': lambda data, arrays:
                ext_types.ExtList(ext_methods.datablock_to_numpy(data)[
                                  0].flatten().tolist()),
                'key': 'ions_per_type',
                # 'type' : ext_types.ExtList,
            },
            r'\n(S.*)\n': {
                'important': False,
                'selection': -1,
                'key': 'selection',
            },
            # r'\nD\w+\n(?:S.*\n)([\s\S]*?)\n\s*\n' : {
            r'\n[dD]\w+\n(\s*\d+[\s\S]*?)\n(?:\s*\n|$)': {
                'prerequisite': ['cell'],
                'important': False,
                'selection': -1,
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data),
                # 'key' : 'direct_position_data',
                'key': [
                    {
                        'key': 'positions',
                        'index': ':,:3',
                        'type': float,
                        'process': lambda data, arrays: data.dot(arrays['cell']),
                    },
                    {
                        'key': 'constraints',
                        'index': ':,3:',
                        # 'type' : bool,
                        'process': lambda data, arrays: np.any(np.logical_or(data == 'F', data == 'False'), axis=1),
                    },
                ],
            },
            # r'\nC\w+\n(?:S.*\n)([\s\S]*?)\n\s*\n' : {
            r'\n[cC]\w+\n(\s*\d+[\s\S]*?)\n(?:\s*\n|$)': {
                'prerequisite': ['scaling_factor'],
                'important': False,
                'selection': -1,
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data),
                'key': [
                    {
                        'key': 'positions',
                        'index': ':,:3',
                        'type': float,
                        'process': lambda data, arrays: data * arrays['scaling_factor'],
                    },
                    {
                        'key': 'constraints',
                        'index': ':,3:',
                        'process': lambda data, arrays: np.any(np.logical_or(data == 'F', data == 'False'), axis=1),
                        # 'type' : bool,
                    },
                ],
            },
            r'\n\s*\n\s*(\w[\s\S]*)': {
                'important': False,
                'selection': -1,
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data),
                'key': 'velocity',
            },
        },
        'synthesized_data': OrderedDict({
            'symbols': {
                # 'debug': True,
                'prerequisite': ['element_types', 'ions_per_type'],
                'equation': lambda arrays: [x for y in [[x]*y for (x, y) in zip(arrays['element_types'], arrays['ions_per_type'])] for x in y],
                'delete': ['element_types', 'ions_per_type'],
            },
        }),
    },
    'DOSCAR': {
        'calculator': 'VASP',
        'file_format': 'plain_text',
        'primitive_data': {
            r'.*\n.*\n.*\n.*\n.*\n.*\n([\s\S]*)': {
                'important': True,
                'selection': -1,
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data),
                'key': 'calc_arrays/doscar',
            },
        },
        'synthesized_data': {},
    },
    'vasp-xml': {
        'calculator': 'VASP',
        'file_format': 'lxml',
        'primitive_data': OrderedDict({
            '(//structure/crystal/varray[@name="basis"])[1]//v//text()': {
                'important': True,
                'join': '\n',
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data),
                'key': 'cell',
            },
            '(//structure/varray[@name="positions"])[last()]//v//text()': {
                'important': True,
                'join': '\n',
                'prerequisite': ['cell'],
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data).dot(arrays['cell']),
                'key': 'positions',
                'type': float,
            },
            '(//structure/varray[@name="positions"])//v//text()': {
                'prerequisite': ['positions'],
                'important': True,
                'join': '\n',
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data).astype(float).dot(arrays['cell']).reshape((-1, len(arrays['positions']), 3)),
                'key': 'all_positions',
                'passerror': True,
                'type': float,
            },
            '//atominfo/array[@name="atoms"]/set/rc/c[1]/text()': {
                'important': True,
                'selection': 'all',
                'key': [
                    {
                        'key': 'symbols',
                        # 'type' : str,
                        'index': ':',
                        'process': lambda data, arrays: [_.strip() for _ in data],
                    },
                ]
            },
            '//atominfo/array[@name="atomtypes"]/set/rc/c[1]/text()': {
                # 'debug' : True,
                'important': True,
                'selection': 'all',
                'process': lambda data, arrays: int(data),
                'type': ext_types.ExtList,
                'key': 'ions_per_type',
            },
            '//atominfo/array[@name="atomtypes"]/set/rc/c[5]/text()': {
                'important': True,
                'selection': 'all',
                'process': lambda data, arrays: data.strip(),
                'type': ext_types.ExtList,
                'key': 'calc_arrays/vasp_pot',
            },
            '(//dos/total)[last()]/array/field/text()': {
                'important': False,
                'selection': 'all',
                'process': lambda data, arrays: data.strip(),
                'key': 'calc_arrays/dos_total_header',
            },
            '(//calculation/energy)[last()]/i[@name="e_fr_energy"]/text()': {
                'important': False,
                'process': lambda data, arrays: data.strip(),
                'type': float,
                'key': 'calc_arrays/e_fr_energy',
            },
            '(//calculation/energy)[last()]/i[@name="e_wo_entrp"]/text()': {
                'important': False,
                'process': lambda data, arrays: data.strip(),
                'type': float,
                'key': 'calc_arrays/potential_energy',
            },
            '(//calculation/energy)[last()]/i[@name="e_0_energy"]/text()': {
                'important': False,
                'process': lambda data, arrays: data.strip(),
                'type': float,
                'key': 'calc_arrays/e_0_energy',
            },
            '//time[@name="totalsc"]/text()': {
                'important': False,
                'selection': 'all',
                # 'join' : '\n',
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data if ' ' in data else data[:len(data)//2]+' '+data[len(data)//2:]),
                # 'type' : np.array,
                'key': 'calc_arrays/total_time'
            },
            '(//varray[@name="forces"])[last()]/v/text()': {
                'important': False,
                'join': '\n',
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data),
                'type': float,
                'key': 'calc_arrays/forces',
            },
            '//varray[@name="forces"]/v/text()': {
                'important': False,
                'join': '\n',
                'prerequisite': ['calc_arrays/forces'],
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data).reshape((-1, \
                                                                                              len(arrays['calc_arrays']['forces']), 3)),
                'type': float,
                'passerror': True,
                'key': 'calc_arrays/all_forces',
            },
            '(//varray[@name="stress"])[last()]/v/text()': {
                'important': False,
                'join': '\n',
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data),
                'type': float,
                'key': 'calc_arrays/stress',
            },
            '//varray[@name="stress"]/v/text()': {
                # 'debug' : True,
                'important': False,
                'prerequisite': ['calc_arrays/stress'],
                'join': '\n',
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data).reshape((-1, \
                                                                                              len(arrays['calc_arrays']['stress']), 3)),
                'type': float,
                'passerror': True,
                'key': 'calc_arrays/all_stress',
            },
            '//dos/total/array/set/set[@comment="spin 1"]/r/text()': {
                'important': False,
                'join': '\n',
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data),
                'type': float,
                'key': 'dos_total_spin1',
            },
            '//dos/total/array/set/set[@comment="spin 2"]/r/text()': {
                'important': False,
                'join': '\n',
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data),
                'type': float,
                'key': 'dos_total_spin2',
            },
            '//dos/partial/array/field/text()': {
                'important': False,
                'selection': 'all',
                'process': lambda data, arrays: data.strip(),
                'key': 'calc_arrays/dos_partial_header',
            },
            '//dos/partial/array/set/set/set[@comment="spin 1"]/r/text()': {
                'important': False,
                'join': '\n',
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data),
                'type': float,
                'key': 'dos_partial_spin1',
            },
            '//dos/partial/array/set/set/set[@comment="spin 2"]/r/text()': {
                'important': False,
                'join': '\n',
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data),
                'type': float,
                'key': 'dos_partial_spin2',
            },
            '(//eigenvalues)[last()]/array/field/text()': {
                'important': False,
                'selection': 'all',
                'process': lambda data, arrays: data.strip(),
                'key': 'calc_arrays/eigenvalues_header',
            },
            '(//eigenvalues)[last()]/array/set/set[@comment="spin 1"]/set[@comment="kpoint 1"]/r/text()': {
                'important': False,
                'join': '\n',
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data),
                'type': float,
                'key': 'calc_arrays/spin1_kpoint1_eigen',
            },
            '(//eigenvalues)[last()]/array/set/set[@comment="spin 1"]/set/r/text()': {
                'important': False,
                'join': '\n',
                'prerequisite': ['calc_arrays/spin1_kpoint1_eigen'],
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data).reshape(\
                    tuple([-1] + list(arrays['calc_arrays']['spin1_kpoint1_eigen'].shape))),
                'type': float,
                'key': 'calc_arrays/spin1_eigen',
            },
            '(//eigenvalues)[last()]/array/set/set[@comment="spin 2"]/set/r/text()': {
                'important': False,
                'join': '\n',
                'prerequisite': ['calc_arrays/spin1_kpoint1_eigen'],
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data).reshape(\
                    tuple([-1] + list(arrays['calc_arrays']['spin1_kpoint1_eigen'].shape))),
                'type': float,
                'key': 'calc_arrays/spin2_eigen',
            },
            '//parameters': {
                'important': True,
                'process': lambda data, arrays: ext_methods.xml_parameters(data),
                'key': 'calc_arrays/parameters',
            },
            '//generator': {
                'important': True,
                'process': lambda data, arrays: ext_methods.xml_parameters(data),
                'key': 'calc_arrays/calc_properties',
            },
            '//kpoints/varray[@name="kpointlist"]/v/text()': {
                'important': True,
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(data),
                'type': float,
                'key': 'calc_arrays/kpoints/kpointlist',
            },
            '//kpoints/varray[@name="weights"]/v/text()': {
                'important': True,
                'process': lambda data, arrays: ext_methods.datablock_to_numpy(''.join(data)),
                'type': float,
                'key': 'calc_arrays/kpoints/weights',
            },
        }),
        'synthesized_data': OrderedDict({
            'calc_arrays/dos/partial/spin1': {
                'prerequisite': ['calc_arrays/dos_partial_header', 'dos_partial_spin1'],
                'equation': lambda arrays: dict(zip(arrays['calc_arrays']['dos_partial_header'], \
                                                    [arrays['dos_partial_spin1'][:, i].reshape((-1, len(arrays['dos_total_spin1']))) \
                                                     for i in range(len(arrays['calc_arrays']['dos_partial_header']))])),
                'delete': ['dos_partial_spin1'],
            },
            'calc_arrays/dos/partial/spin2': {
                'prerequisite': ['calc_arrays/dos_partial_header', 'dos_partial_spin2'],
                'equation': lambda arrays: dict(zip(arrays['calc_arrays']['dos_partial_header'], \
                                                    [arrays['dos_partial_spin2'][:, i].reshape((-1, len(arrays['dos_total_spin1']))) \
                                                     for i in range(len(arrays['calc_arrays']['dos_partial_header']))])),
                'delete': ['dos_partial_spin2'],
            },
            'calc_arrays/dos/total/spin1': {
                # 'debug' : True,
                'prerequisite': ['calc_arrays/dos_total_header', 'dos_total_spin1'],
                'equation': lambda arrays: dict(zip(arrays['calc_arrays']['dos_total_header'], \
                                                    [arrays['dos_total_spin1'][:, i] for i in range(len(arrays['calc_arrays']['dos_total_header']))])),
                'delete': ['dos_total_spin1'],
            },
            'calc_arrays/dos/total/spin2': {
                'prerequisite': ['calc_arrays/dos_total_header', 'dos_total_spin2'],
                'equation': lambda arrays: dict(zip(arrays['calc_arrays']['dos_total_header'], \
                                                    [arrays['dos_total_spin2'][:, i] for i in range(len(arrays['calc_arrays']['dos_total_header']))])),
                'delete': ['dos_total_spin2'],
            },
            'calc_arrays/pseudopotential': {
                'prerequisite': ['ions_per_type', 'calc_arrays/vasp_pot'],
                # 'equation': lambda arrays: [x for y in [[x]*y for (x, y) in zip(arrays['calc_arrays']['vasp_pot'], arrays['ions_per_type'])] for x in y],
                'equation': lambda arrays: format_pseudopotential(arrays),
                # 'delete': ['vasp_pot', 'ions_per_type'],
            },
        }),
    },
    'INCAR': {
        'parser_type': 'customized',
        'parser': parse_INCAR,
        # 'ignorance': ('#', ),
        # 'file_format': 'dict',
        # 'destination': 'calc_arrays/vasp_input',
        'non_regularize': True,
    }
}
