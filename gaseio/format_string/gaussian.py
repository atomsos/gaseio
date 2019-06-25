"""
format_string
"""

import re
from collections import OrderedDict
from io import StringIO

import math
import numpy as np
import pandas as pd

import chemdata
import atomtools
from atomtools import Status


from .. import ext_types
from .. import ext_methods


ENERGY_ORDER = [
                r"CCSD\(?T\)?",
                r"CCSD", 
                r"CBSQ", 
                r"QCISD\(?T\)?", 
                r"QCISD", 
                r"MP4\(?SDQ\)?", 
                r"MP4\(?DQ\)?", 
                r"MP4\(?D\)?", 
                r"MP3", 
                r"MP2", 
                r"HF",
                ]


def get_value_by_order(properties, order):
    if properties is None:
        return None
    for _ord in order:
        # if properties.get(_ord, None):
        #     return properties.get(_ord)
        for item, val in properties.items():
            if re.match(_ord+'.*', item):
                return val

def gaussian_extract_frequency(logline, arrays):
    """
    extract frequency data from gaussian log
    """

    item_pattern = r'\s+(.*?)\s*-- '
    def parse_freq_lines(origin_lines, startline, num_lines, 
                         index, num_items, natoms, mode=3):
        """
        #           1              2              3
        #           A              A              A
        #  Frequencies --   -754.3221            31.3611           174.9690
        #  Red. masses --      1.1484             6.5519             6.8477
        #  Frc consts  --      0.3850             0.0038             0.1235
        #  IR Inten    --   1827.3164             2.1140             0.0189
        #   Atom  AN      X  Y  Z    X  Y      Z    X      Y      Z
        #      1  15     0.00   0.05   0.00 0.00   0.00  -0.01     0.10   0.04   0.00
        #      2   6     0.00  -0.02   0.00    -0.20  -0.01   0.15     0.21  -0.09  -0.06
        #      3   1     0.00   0.00   0.00    -0.33  -0.03   0.07     0.29   0.03   0.00
        #      4   1    -0.01  -0.02  -0.02    -0.20  -0.01   0.24     0.39  -0.18  -0.14
        ------------------------
        #                            1         2         3         4         5
        #                            A         A         A         A         A
        #        Frequencies ---    86.8799  208.9974  344.3601  420.4250  423.0281
        #     Reduced masses ---     2.6364    1.3937    2.5278    3.1416    3.1471
        #    Force constants ---     0.0117    0.0359    0.1766    0.3272    0.3318
        #     IR Intensities ---     0.0000    0.0000    0.0000    0.0000    0.0000
        #  Coord Atom Element:
        #    1     1     6          0.00000   0.00000   0.00000  -0.12239   0.00000
        #    2     1     6          0.00000   0.00000   0.00000   0.08728   0.00000
        #    3     1     6          0.15124   0.00129  -0.00579   0.00000   0.00101
        #    1     2     6          0.00000   0.00000   0.00000  -0.08238   0.00000
        #    2     2     6          0.00000   0.00000   0.00000   0.12674   0.00000
        #    3     2     6          0.16741  -0.01933  -0.14943   0.00000   0.23508

        """
        assert mode in [3, 5]
        item_dict = {
            'Frequencies' : 'frequency',
            'Red. masses' : 'reduced_mass',
            'Frc consts'  : 'force_constant',
            'IR Inten'    : 'IR_intensity',
            'Raman Activ' : 'Raman_Activity',
            'Depolar (P)' : 'Depolar_p',
            'Depolar (U)' : 'Depolar_u',
        }
        lines = origin_lines[startline: startline+num_lines]
        # import pdb; pdb.set_trace()
        # if DEBUG: print('line:', lines)
        if index+1 > len(lines[0].split()):
            return None
        data = {}
        line_i = 1
        data['symmetry'] = lines[line_i].split()[index]
        line_i += 1
        # print('\n'.join(lines))
        for line in lines[line_i:num_items+line_i]:
            item_name, rs = line.split('--')
            # item_name, rs = re.split(r'-{2,}', line)
            item_name = item_name.strip()
            item_name = item_dict.get(item_name, None) or item_name
            rs = rs.strip().split()[index]
            rs = float(rs)
            data[item_name] = rs
        line_i += num_items+1
        #   vector = [[0.0, 0.0, 0.0]] *natoms
        vector = {}
        for line in lines[line_i:]:
            try:
                atom_number = int(line[0:14].split()[0]) -1
            except:
                break
            i_vector = line.split()[2+3*index:2+3*index+3]
            i_vector = list(map(lambda x: float(x), i_vector))
            # if DEBUG: print(i_vector)
            # vector.append(i_vector)
            vector[atom_number] = i_vector
            # if DEBUG: print(atom_number, i_vector)
        data['vector'] = vector
        return data


    # import pdb; pdb.set_trace()
    # print(logline)
    lines = logline.strip().split('\n')
    # natoms = len(arrays['positions'])
    natoms_pattern = r'  Atom  [\s\S]*?(?:                     |$)'
    string = re.findall(natoms_pattern, logline)
    natoms = len(string[0].strip().split('\n')) - 1
    
    items_name = set(re.findall(item_pattern, logline))
    num_line_each = 2 + len(items_name) + 1 + natoms

    N_freq_per_block = 3
    freq = []
    for i in range(math.floor(natoms/N_freq_per_block)):
        for j in range(N_freq_per_block):
            data = parse_freq_lines(lines, num_line_each*i,
                num_line_each, j, len(items_name), natoms)
            if data is None:
                break
            # if DEBUG: print(i, j, data)
            freq.append(data)
        if data is None:
            break
    return freq







def get_block_data(line, columns=None, index_col=False, header=None):
    csv = pd.read_csv(StringIO(line), sep=r'\s+', index_col=index_col, header=header)
    if columns is None:
        return np.array(csv)
    # data = np.array(csv)[:,columns]
    data = np.array(csv.ix[:,columns])
    #try:
    #  data[np.isnan(data)] = 0.
    #except:
    #  pass
    return data


def parse_diagonal_data(inp_line, ndim, max_width,
    has_top = True, sindex=1, type='lower'):
    lines = inp_line.split('\n')
    row_i = line_i = 0
    xndim = ndim
    if has_top:
        header_line = 1
    else:
        header_line = 0
    outdata = np.zeros((ndim, ndim))
    # outdata[:] = np.nan
    while row_i < ndim:
        line = '\n'.join(lines[line_i:line_i+xndim+header_line])
        line = re.sub('^', '^XX ', line)
        line = re.sub('D(?=\+|\-)', 'E', line)
        data = get_block_data(line, index_col=0, header=header_line-1)
        outdata[row_i: ndim, row_i: min(row_i+max_width, ndim)] = data
        row_i += max_width
        row_i = min(row_i, ndim)
        line_i += xndim +header_line
        xndim -= max_width
    outdata[np.isnan(outdata)] = 0
    outdata += np.triu(outdata.T, 1)
    return outdata



def gaussian_extract_second_derivative_matrix(logline, arrays):
    # import pdb; pdb.set_trace()
    if re.match(r'[\s\S]*?X1\s+Y1\s+Z1[\s\S]*?', logline):
        arrays['hessian_type'] = 'Cartesian'
        natoms = len(arrays['positions'])
        ndim = 3*natoms
    else:
        arrays['hessian_type'] = 'Internal'
        ndim = len(arrays['calc_arrays/internal_coords'])
    return parse_diagonal_data(logline, ndim=ndim, max_width=5)

# def second_order_forces_consts(logline, fctype, ndim):
#     if fctype == 'cartesian':
#         if ' Force constants in Cartesian coordinates:' in logline:
#             return parse_diagonal_data(logline,
#                 ' Force constants in Cartesian coordinates: \n',
#                 '\n FormGI is forming the', ndim=ndim, max_width=5)
#     else:
#         if ' Force constants in internal coordinates:' in logline:
#             ndim = len(get_internal_coordinations(logline))
#             return parse_diagonal_data(logline,
#                 ' Force constants in internal coordinates: \n',
#                 '\n Leave Link  716 at', ndim=ndim, max_width=5)



def process_population_analysis(data, ndim, drop_length=None, rm_header_regex=r' {20,}\d.*\n', dtype='square'):
    # import pdb; pdb.set_trace()
    assert dtype in ['square', 'lower_triangular']
    drop_pattern = re.compile('^.{%d}|\n.{%d}' %(drop_length, drop_length))
    data = re.sub(drop_pattern, '\n', re.sub(rm_header_regex, '', data)).strip()
    # print(data)
    lines = data.split('\n')
    max_width = max([len(_.split()) for _ in lines])
    if dtype == 'square':
        for i in range(ndim):
            lines[i] = ' '.join(lines[i::ndim])
    elif dtype == 'lower_triangular':
        block_length = ndim % max_width
        end_point = 0
        while block_length < ndim:
            for i in range(1, block_length+1):
                x1 = (end_point+i+block_length)
                x2 = (end_point+i)
                # print(len(lines), x2, x1, block_length, end_point)
                lines[-x1] += ' ' + lines[-x2]
            end_point += block_length
            block_length += max_width
    header = ' '.join(str(_) for _ in range(ndim))
    newdata = header + '\n' + '\n'.join(lines[:ndim])
    # print('newdata', newdata)
    outdata = ext_methods.datablock_to_numpy(newdata, header=0)
    if dtype != 'square':
        # print(outdata)
        outdata[np.isnan(outdata)] = 0
        outdata += np.triu(outdata.T, 1)
    return outdata



def process_orbital_basis(data):
    pattern = r'^ *\d+ '
    data = [re.sub(pattern, '', _[:20].strip()) for _ in data.split('\n')]
    for i in range(1, len(data)):
        length = len(re.match(r'^ *', data[i])[0])
        data[i] = data[i-1][:length] + data[i][length:]
    return data

FORMAT_STRING = {
    'gaussian': {
        'calculator': 'Gaussian',
        'primitive_data' : {
            r'%npro.*=(\d+)\s*\n' : {
                    'important': False,
                    'selection' : -1,
                    'type': int,
                    'key' : 'maxcore',
            },
            r'%mem.*=(\d+.*)\s*\n' : {
                    'important': False,
                    'selection' : -1,
                    'type': str,
                    'key' : 'maxmem',
            },
            r'#\s*([\s\S]*?)\n\s*\n' : {
                    'important': True,
                    'selection' : 0,
                    'type': str,
                    'key' : 'calc_arrays/command',
                    'process' : lambda data, arrays: data.replace('\n', ' ').strip(),
            },
            r'#\s*[\s\S]*?\n\s*\n([\s\S]*?)\n\s*\n' : {
                    'important' : True,
                    'selection' : 0,
                    'type' : str,
                    'key' : 'comments',
                    'process' : lambda data, arrays: data.replace('\n', ' ').strip(),
            },
            r'#\s*[\s\S]*?\n\s*\n[\s\S]*?\n\s*\n\s*([+-]?\d+)[, ]*\d+.*' : {
                    'important' : True,
                    'selection' : 0,
                    'type' : int,
                    'key' : 'charge'
            },
            r'#\s*[\s\S]*?\n\s*\n[\s\S]*?\n\s*\n\s*[+-]?\d+[, ]*(\d+).*' : {
                    'important' : True,
                    'selection' : 0, 
                    'type' : int,
                    'key' : 'multiplicity'
            },
            r'\n\s*[+-]?\d+[, ]*\d+.*\s*\n([\s\S]*?)\n\s*\n' : {
                    'important' : True,
                    'selection' : 0, 
                    'process' : lambda data, arrays: ext_methods.datablock_to_numpy(data),
                    'key' : 'gaussian_coord_datablock',
                    # 'key' : [
                    #     {
                    #         'key' : 'symbols',
                    #         'type' : str,
                    #         'index' : ':,0',
                    #         'process' : lambda data, arrays: ext_types.ExtList(data.tolist()),
                    #     },
                    #     {
                    #         'key' : 'positions',
                    #         'type' : float,
                    #         'index' : ':,1:4',
                    #     },
                    #     {
                    #         'key' : 'tags',
                    #         'type' : str,
                    #         'index' : ':,4',
                    #     },
                    # ],
            },
            r'\n\s*[+-]?\d+[, ]*\d+.*\s*\n[\s\S]*?\n\s*\n([\s\S]*)' : {
                    'important' : True,
                    'selection' : -1,
                    'type' : str,
                    'key' : 'calc_arrays/appendix'
            },
            r'#[\s\S]*?connectivity[\s\S]*?\n\n[\s\S]*?\n\s*\n\s*([\d\n\. ]*)\n\n':{
                    'important': False,
                    'selection' : -1,
                    'type' : str,
                    'key' : 'calc_arrays/connectivity',
            },
            r'#[\s\S]*?gen[\s\S]*?\n\n[\s\S]*?\n\s*\n\s*[\d\n\. ]*\n\n([A-Z][a-z]?[\s\S]*?\n\n[A-Z][a-z]?.*\d\n[\s\S]*?)\n\n':{
                    'important': False,
                    'selection' : -1,
                    'type' : str,
                    'key' : 'calc_arrays/genecp',
            },
            r'(\$NBO.*\$END)':{
                    'important': False,
                    'selection' : -1,
                    'type' : str,
                    'key' : 'calc_arrays/nbo',
            },
            },
        'synthesized_data' : OrderedDict({
            'symbols' : {
                'prerequisite' : ['gaussian_coord_datablock'],
                'equation' : lambda arrays: ext_types.ExtList(arrays['gaussian_coord_datablock'][:,0].flatten().tolist()),
            },
            'constraint' : {
                'prerequisite' : ['gaussian_coord_datablock'],
                'condition' : lambda arrays: arrays['gaussian_coord_datablock'].shape[1] >= 5 and \
                                             np.logical_or(arrays['gaussian_coord_datablock'][:,1]==0, arrays['gaussian_coord_datablock'][:,1]==-1).all(),
                'equation' : lambda arrays: arrays['gaussian_coord_datablock'][:,1] == -1,
            },
            'positions' : {
                'prerequisite' : ['gaussian_coord_datablock'],
                'equation' : lambda arrays: arrays['gaussian_coord_datablock'][:,2:5] if 'constraint' in arrays else arrays['gaussian_coord_datablock'][:,1:4],
            },
            'tags' : {
                'prerequisite' : ['gaussian_coord_datablock'],
                'condition' : lambda arrays: arrays['gaussian_coord_datablock'].shape[1] >= 6 if 'constraint' in arrays else \
                                             arrays['gaussian_coord_datablock'].shape[1] >= 5,
                'equation' : lambda arrays: arrays['gaussian_coord_datablock'][:,5] if 'constraint' in arrays else \
                                            arrays['gaussian_coord_datablock'][:,4],
                'delete' : ['gaussian_coord_datablock'],
            },
            }),
    },
    'gaussian-out': {
        'calculator': 'Gaussian',
        'primitive_data': OrderedDict({
            r'Charge\s+=\s+(-?\d+)' : {
                'important' : False,
                'selection' : -1,
                'key' : 'charge',
                'type' : int,
            },
            r'Multiplicity\s+=\s+(\d+)' : {
                'important' : False,
                'selection' : -1,
                'key' : 'multiplicity',
                'type' : int,
            },
            r'\n (1[\\|\|]1[\\|\|][\s\S]*?[\\|\|]\s*[\\|\|])\s*@\n': {
                # 'important' : True,
                'selection' : -1,
                'key' : 'gaussian_datastring',
                'type' : str,
                'process' : lambda data, arrays: data.replace('\n ', '').replace('\\', '|').strip()
            },
            r'Center.* Atomic *Atomic *Coordinates.*\(.*\).*\n.*\n\s*-*\s*\n([\s\S]*?)\n\s*-+\s*\n' : {
                'important' : True,
                'selection' : -1,
                'process' : lambda data, arrays: ext_methods.datablock_to_numpy(data),
                'key' : [
                    {
                        'key' : 'numbers',
                        'type' : int,
                        'index' : ':,1',
                    },
                    {
                        'key' : 'positions',
                        'type' : float,
                        'index' : ':,3:',
                    }
                    ],
            },
            r'\n Dipole moment.*\n\s*(X=\s+.*)\n': {
                'important' : False,
                'selection' : -1,
                'process' : lambda data, arrays: ext_methods.datablock_to_numpy(data),
                'key' : [
                    {
                        'key' : 'calc_arrays/dipole_moment',
                        'type' : float,
                        'index' : '[0],[1,3,5]',
                        'postprocess': lambda x: x.flatten()
                    },
                    ],
            },
            r'\n Quadrupole moment.*\n\s*(XX=\s+.*\n.*)\n': {
                'important' : False,
                'selection' : -1,
                'process' : lambda data, arrays: ext_methods.datablock_to_numpy(data),
                'key' : [
                    {
                        'key' : 'calc_arrays/quadrupole_moment',
                        'type' : float,
                        'index' : ':,[1,3,5]',
                    }
                    ],
            },
            r'and normal coordinates:\n[\s\S]*? {20,}([\s\S]*?)\n -{10,}\n - Thermochemistry -' : {
                # 'debug' : True,
                'important' : False,
                'selection' : -1,
                'process' : lambda data, arrays: gaussian_extract_frequency(data.split('coordinates:\n')[-1], arrays),
                'key' : 'calc_arrays/frequency',
            },
            r'Initial Parameters[\s\S]*?Name.*\n\s-*\n([\s\S]*?)\n\s----*': {
                # 'debug' : True,
                'important' : False,
                'selection' : -1,
                'process' : lambda data, arrays: ext_methods.datablock_to_numpy(data.replace('!', ' '), sep='\s+'),
                'key' : [
                    {
                        'key' : 'calc_arrays/internal_coords',
                        'type' : str,
                        'index' : ':,0',
                    },
                    # {
                    #     'key' : 'calc_arrays/internal_coords_definition',
                    #     'type' : str,
                    #     'index' : ':,2',
                    # },
                    # {
                    #     'key' : 'calc_arrays/internal_coords_value',
                    #     'type' : float,
                    #     'index' : ':,3',
                    # },
                    ]
            },
            r' The second derivative matrix:\n([\s\S]*?)\n ITU' : {
                'important' : False,
                'selection' : -1,
                'process' : lambda data, arrays: gaussian_extract_second_derivative_matrix(data, arrays),
                'key' : 'Hessian',
            },
            r'Normal termination' : {
                'important' : False,
                'selection' : 'all',
                'key' : 'normal_termination',
            },
            r'Error termination' : {
                'important' : False,
                'selection' : 'all',
                'key' : 'error_termination',
            },
            r'SCF Done:  E\(.*?\)\s=\s*([+-]?\d+\.\d+E?[+-]?[0-9]*)\s+' : {
                'important' : False,
                'selection' : -1,
                'key' : 'possible_potential_energy',
                'type' : float,
            },
            r'Center     Atomic {10,}Forces[\s\S]*?-{10,}\n([\s\S]*?)-{10,}' : {
                'important' : False,
                'selection' : -1,
                'process' : lambda data, arrays: ext_methods.datablock_to_numpy(data),
                'key' : [
                    {
                        'key' : 'calc_arrays/forces',
                        'index' : ':,2:5',
                        'process' : lambda data, arrays: data * atomtools.unit.trans_force('au', 'eV/Ang'),
                    },
                    ],
            },
            r'electronic state is (.*?)\.' : {
                'important' : False,
                'selection' : -1,
                'key' : 'calc_arrays/electronic_state',
            },
            r'Alpha  occ. eigenvalues --(.*?)\n' : {
                'important' : False,
                'selection' : 'all',
                'key' : 'calc_arrays/occupied_eigenvalues',
                'join' : ' ',
                'process' : lambda data, arrays : ext_methods.datablock_to_numpy(data),
            },
            r'Alpha virt. eigenvalues --(.*?)\n' : {
                'important' : False,
                'selection' : 'all',
                'key' : 'calc_arrays/virtual_eigenvalues',
                'join' : ' ',
                'process' : lambda data, arrays : ext_methods.datablock_to_numpy(data),
            },
            r'Molecular Orbital Coefficients:\n[\s\S]*?Eigenvalues.*\n([\s\S]*?)\n {20,}' : {
                'important' : False,
                'selection' : -1,
                'process' : lambda data, arrays: process_orbital_basis(data),
                'key' : 'calc_arrays/orbital_basis',
            },
            r'Molecular Orbital Coefficients:\n([\s\S]*?)\n.*Density Matrix:' : {
                # 'debug' : True,
                'important' : False,
                'selection' : -1,
                'process' : lambda data, arrays: process_population_analysis(\
                                                 re.sub(r'.*[OV].*\n.*Eigenvalues.*\n', '', data),
                                                 len(arrays['calc_arrays/orbital_basis']), 20, rm_header_regex=r' {20,}\d.*\n'),
                'key' : 'calc_arrays/molecular_orbital',
            },
            r'Density Matrix:\n([\s\S]*?)\n.*Full Mulliken population analysis:' : {
                'important' : False,
                'selection' : -1,
                'process' : lambda data, arrays: process_population_analysis(data,
                                                 len(arrays['calc_arrays/orbital_basis']), 20, rm_header_regex=r' {20,}\d.*\n',
                                                 dtype='lower_triangular'),
                'key' : 'calc_arrays/density_matrix'
            },
            r'Full Mulliken population analysis:\n([\s\S]*?)\n.*Gross orbital populations' : {
                'important' : False,
                'selection' : -1,
                'process' : lambda data, arrays: process_population_analysis(data,
                                                 len(arrays['calc_arrays/orbital_basis']), 20, rm_header_regex=r' {20,}\d.*\n',
                                                 dtype='lower_triangular'),
                'key' : 'calc_arrays/mulliken_population'
            },
            r'Gross orbital populations:\n([\s\S]*?)\n.*Condensed to atoms (all electrons):' : {
                'important' : False,
                'selection' : -1,
                'process' : lambda data, arrays: ext_methods.datablock_to_numpy(re.sub(r'\n.{20}', '\n', data)[data.index('\n'):]).flatten(),
                'key' : 'calc_arrays/gross_orbital_population'
            },
            r'Condensed to atoms.*all electrons.*:\n([\s\S]*?)\n.*Mulliken charges:' : {
                'important' : False,
                'selection' : -1,
                'process' : lambda data, arrays: process_population_analysis(data,
                                                 len(arrays['positions']), 12, rm_header_regex=r' {12,}\d.*\n'),
                'key' : 'calc_arrays/condense_to_atoms'
            },
            r'Mulliken charges:([\s\S]*?)\n.*Sum of Mulliken charges' : {
                'important' : False,
                'selection' : -1,
                'process' : lambda data, arrays: ext_methods.datablock_to_numpy(re.sub(r'\n.{10}', '\n', data)[data.index('\n'):]).flatten(),
                'key' : 'calc_arrays/mulliken_charge'
            },
            }),
        'synthesized_data' : OrderedDict({
            'calc_arrays/status' : {
                'equation' : lambda arrays: Status.error if 'error_termination' in arrays else \
                                            Status.complete if 'normal_termination' in arrays else \
                                            Status.running if atomtools.file.file_active(arrays['absfilename']) else\
                                            Status.stopped,
                'delete' : ['error_termination', 'normal_termination'],
            },
            'symbols' : {
                'prerequisite' : ['numbers'],
                'equation' : lambda arrays: np.array([chemdata.get_element(_) for _ in arrays['numbers']]),
                'process' : lambda data, arrays: ext_types.ExtList(data.tolist()),
            },
            'gaussian_datablock' : {
                'prerequisite' : ['gaussian_datastring'],
                'equation' : lambda arrays: arrays['gaussian_datastring'].split('||'),
            },
            'calc_arrays/config' : {
                'prerequisite' : ['gaussian_datablock'],
                'equation' : lambda arrays: arrays['gaussian_datablock'][0],
            },
            'calc_arrays/command' : {
                'prerequisite' : ['gaussian_datablock'],
                'equation' : lambda arrays: re.match(r'\s*#\s*(.*?)$', arrays['gaussian_datablock'][1])[1],
            },
            'comments' : {
                'prerequisite' : ['gaussian_datablock'],
                'equation' : lambda arrays: arrays['gaussian_datablock'][2],
            },
            'gaussian_datablock_geometry' : {
                'prerequisite' : ['gaussian_datablock'],
                'equation' : lambda arrays: arrays['gaussian_datablock'][3],
            },
            'calc_arrays/results' : {
                'prerequisite' : ['gaussian_datastring'],
                'equation' : lambda arrays: ext_methods.string_to_dict(re.findall(r'\|\|(Version=.*?)\|\|', 
                                            arrays['gaussian_datastring'])[-1]),
                'delete' : ['gaussian_datastring'],
            },
            'calc_arrays/potential_energy' : {
                # 'debug' : True,
                # 'prerequisite' : ['possible_potential_energy'],
                'condition' : lambda arrays: arrays.get('calc_arrays/results', None) is not None or\
                                             arrays.get('possible_potential_energy', None) is not None,
                'equation' : lambda arrays: float(get_value_by_order(arrays.get('calc_arrays/results', None), 
                                                  ENERGY_ORDER) or arrays.get('possible_potential_energy', None))\
                                            * atomtools.unit.trans_energy('au', 'eV'),
                'delete' : ['possible_potential_energy'],
            },
            'calc_arrays/zero_point_energy' : {
                'prerequisite' : ['calc_arrays/results/ZeroPoint'],
                'equation' : lambda arrays: float(arrays['calc_arrays/results/ZeroPoint']) *\
                                            atomtools.unit.trans_energy('au', 'eV'),
            },
            'charge' : {
                'prerequisite' : ['gaussian_datablock_geometry'],
                'equation' : lambda arrays: int(arrays['gaussian_datablock_geometry'].split('|')[0].split(',')[0]),
            },
            'multiplicity' : {
                'prerequisite' : ['gaussian_datablock_geometry'],
                'equation' : lambda arrays: int(arrays['gaussian_datablock_geometry'].split('|')[0].split(',')[1]),
            },
            }),
    },
}

