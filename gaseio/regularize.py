"""
regularize arrays



"""
import sys
import numpy as np
import chemdata
import inspect
import logging

import atomtools.geo
from ase.symbols import Symbols as ASESymbols
import libmsym.interfaces


current_module = sys.modules[__name__]


logging.basicConfig()
logger = logging.getLogger(__name__)


def reg_customized_symbols(arrays):
    from . import ext_methods
    if 'customized_symbols' in arrays and not 'symbols' in arrays:
        arrays['symbols'] = ext_methods.regularize_symbols(
            arrays['customized_symbols'])


def reg_symbols(arrays):
    from . import ext_methods
    arrays['symbols'] = ext_methods.regularize_symbols(arrays['symbols'])


def reg_positions(arrays):
    arrays['positions'] = np.array(arrays['positions']).reshape((-1, 3))


def reg_numbers_symbols(arrays):
    if 'numbers' in arrays:
        arrays['symbols'] = [chemdata.get_element(
            _) for _ in arrays['numbers']]
    else:
        assert 'symbols' in arrays, 'either numbers or symbols should be in the arrays'
        reg_symbols(arrays)
        arrays['numbers'] = np.array(
            [chemdata.get_element_number(_) for _ in arrays['symbols']])
    arrays['numbers'] = np.array(arrays['numbers'])
    # set chemical_formula
    _symbols_obj = ASESymbols(arrays['numbers'])
    formula_modes = ['all', 'reduce', 'hill', 'metal']
    formula_content = [_symbols_obj.get_chemical_formula(
        mode) for mode in formula_modes]
    arrays['chemical_formula_dict'] = dict(zip(formula_modes, formula_content))
    arrays['chemical_formula'] = arrays['chemical_formula_dict']['hill']


def reg_masses(arrays):
    if not 'masses' in arrays:
        arrays['masses'] = np.array(
            [chemdata.get_element_mass(x) for x in arrays['numbers']])


def reg_charge(arrays):
    if not 'charge' in arrays:
        arrays['charge'] = 0


def reg_spin(arrays):
    if 'multiplicity' in arrays:
        arrays['spin'] = int(arrays['multiplicity']) - 1
    if not 'spin' in arrays:  # auto min spin
        arrays['spin'] = int(sum((arrays['numbers']) - arrays['charge'])) % 2
    arrays['multiplicity'] = arrays['spin'] + 1


def reg_comments(arrays):
    if not 'comments' in arrays:
        arrays['comments'] = 'Generated by GASEIO'
    elif isinstance(arrays['comments'], list):
        arrays['comments'] = ' '.join(arrays['comments'])


def reg_atoms_size(arrays):
    if 'positions' in arrays:
        atoms_size = atomtools.geo.get_atoms_size(arrays['positions'])
        arrays['atoms_size'] = atoms_size


def reg_pbc(arrays):
    if not 'pbc' in arrays:
        arrays['pbc'] = np.array([False] * 3)
    elif isinstance(arrays['pbc'], bool):
        arrays['pbc'] = np.array([arrays['pbc']] * 3)
    else:
        assert isinstance(arrays['pbc'], (tuple, list, np.ndarray))
        arrays['pbc'] = np.array(arrays['pbc'])
        assert arrays['pbc'].shape == (3,)


def reg_calc_arrays(arrays):
    if not 'calc_arrays' in arrays:
        arrays['calc_arrays'] = dict()


def reg_cell(arrays):
    # if not 'cell' in arrays:
    #     arrays['cell'] = np.array([max(x, 21) for x in arrays['atoms_size']])
    #     if not 'celldisp' in arrays:
    #         arrays['celldisp'] = -1 * arrays['cell']/2
    if 'cell' in arrays:
        if arrays['cell'].shape == (3, ):
            arrays['cell'] = np.diag(arrays['cell'])
        if not 'celldisp' in arrays:
            arrays['celldisp'] = np.zeros((3,))


def reg_constraints(arrays):
    if not 'constraints' in arrays:
        arrays['constraints'] = []
    if isinstance(arrays['constraints'], np.ndarray):
        arrays['constraints'] = arrays['constraints'].tolist()


def reg_tags(arrays):
    if not 'tags' in arrays:
        arrays['tags'] = [None] * len(arrays['numbers'])


def reg_initial_things(arrays):
    if not 'initial_magnetic_moments' in arrays:
        arrays['initial_magnetic_moments'] = np.zeros(
            (len(arrays['numbers']),))
    if not 'initial_charges' in arrays:
        arrays['initial_charges'] = np.zeros((len(arrays['numbers']),))


def reg_info(arrays):
    if not 'info' in arrays:
        arrays['info'] = {}


def reg_energy(arrays):
    if not 'kinetic_energy' in arrays:
        arrays['kinetic_energy'] = 0.0
    if 'calc_arrays' in arrays:
        if 'potential_energy' in arrays['calc_arrays']:
            arrays['calc_arrays']['energy'] = arrays['calc_arrays']['potential_energy']


def reg_velocities(arrays):
    if not 'velocities' in arrays:
        natoms = len(arrays['numbers'])
        arrays['velocities'] = np.zeros((natoms, 3))


def num_unit(target, dest):
    num_map = {
        'B': 1,
        'KB': 2**10,
        'MB': 2**20,
        'GB': 2**30,
        'TB': 2**40,
    }
    return num_map[target.upper()] / num_map[dest.upper()]


def reg_memory(arrays):
    if 'calc_arrays' in arrays and 'max_memory' in arrays['calc_arrays']:
        max_memory = arrays['calc_arrays']['max_memory']
        if isinstance(max_memory, str):
            if max_memory.isdigit():
                max_memory = int(max_memory)
            elif max_memory.lower().endswith('b'):
                max_memory = int(
                    int(max_memory[:-2]) * num_unit(max_memory[-2:], 'GB'))
                if max_memory < 1:
                    max_memory = 1
            else:
                raise ValueError(
                    'max_memory must be an integer or integer+KB/MB/GB')
            arrays['calc_arrays']['max_memory'] = max_memory


reg_functions = [
    reg_customized_symbols,
    reg_numbers_symbols,
    reg_positions,
    reg_masses,
    reg_charge,
    reg_spin,
    reg_comments,
    reg_atoms_size,
    reg_cell,
    reg_pbc,
    reg_calc_arrays,
    reg_constraints,
    reg_tags,
    reg_initial_things,
    reg_info,
    reg_energy,
    reg_memory,
]

# all_functions = inspect.getmembers(current_module)
# reg_functions = dict([o for o in all_functions
#                       if inspect.isfunction(o) and o[0].startswith('reg_')])


def libmsymm_symmetry(arrays):
    try:
        results = libmsym.interfaces.get_symmetry_info(arrays)
        arrays['#libmsym'] = results
    except Exception as e:
        pass


def regularize_arrays(arrays):
    if isinstance(arrays, list):
        for arr in arrays:
            regularize_arrays(arr)
        return
    for func in reg_functions:
        func(arrays)
    libmsymm_symmetry(arrays)
