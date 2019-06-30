"""
using jinja2 to generate input files.
Templates are stored in INPUT_TEMPLATE_DIR
"""



import os
import jinja2
import json_tricks

from . import ext_types
from .regularize import regularize_arrays


BASEDIR = os.path.dirname(os.path.abspath(__file__))
INPUT_TEMPLATE_DIR = 'input_templates'

jinja_temp_env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(BASEDIR, INPUT_TEMPLATE_DIR)),
                                    lstrip_blocks=True)



def generate_input_content(arrays, filetype):
    jinja_temp_env.trim_blocks = True
    template_name = filetype + '.j2'
    template = jinja_temp_env.get_template(template_name)
    if not isinstance(arrays, dict) and hasattr(arrays, 'get_positions'):
        module_name = arrays.__class__.__module__
        if module_name == 'ase.atoms':
            atoms = arrays
            calc = atoms.calc
            arrays = atoms.arrays.copy()
            arrays['symbols'] = ext_types.ExtList(atoms.get_chemical_symbols())
            if calc is not None:
                arrays['calc_arrays'] = {}
                arrays['calc_arrays'].update(calc.parameters)
                arrays['calc_arrays'].update(calc.results)
        # if module_name == 'ase.atoms':
        else: # gase
            arrays = arrays.arrays
    regularize_arrays(arrays)
    output = template.render(arrays=arrays, arrays_json=json_tricks.dumps(arrays), **arrays)
    return output

def preview(arrays, filetype):
    print('\n\n\n-------preview start from here------')
    print(generate_input_content(arrays, filetype))


def generate_inputfile(arrays, filetype, inputfilename):
    output = generate_input_content(arrays, filetype)
    with open(inputfilename, 'w') as fd:
        fd.write(output)



