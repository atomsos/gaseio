# GASEIO

Generalized Atomic Simulation Environment Input/Output

Split from GASE project



## Motivation

Using highly extensive code to read all kinds of chemical files, transform to a Atoms object.



## Core idea

Regular expression is the core to parse all files.




## Parse(Reverse format)

Python module [parse](https://github.com/r1chardj0n3s/parse) for Fix Format 



## Supported Formats

* xyz
* json
* gromacs/.gro [http://manual.gromacs.org/archive/5.0.3/online/gro.html]
* .gjf/.com gaussian input file
* .log/.out gaussian output file/adf output file/nwchem output file
* .top/.itp gromacs topology file
* .vasp/POSCAR/CONTCAR/ vasp POSITION file
* OUTCAR vasp OUTPUT file
* vasprun.xml vasprun xml file



## VASPPOT


default vasp potential 




```json
{
  "Ac": "Ac",
  "Ag": "Ag",
  "Al": "Al",
  "Am": "Am",
  "Ar": "Ar",
  "As": "As",
  "At": "At_d",
  "Au": "Au",
  "B": "B",
  "Ba": "Ba_sv",
  "Be": "Be",
  "Bi": "Bi_d",
  "Br": "Br",
  "C": "C",
  "Ca": "Ca_sv",
  "Cd": "Cd",
  "Ce": "Ce",
  "Cl": "Cl",
  "Cm": "Cm",
  "Co": "Co",
  "Cr": "Cr_pv",
  "Cs": "Cs_sv",
  "Cu": "Cu",
  "Dy": "Dy_3",
  "Er": "Er_3",
  "Eu": "Eu_2",
  "F": "F",
  "Fe": "Fe",
  "Fr": "Fr_sv",
  "Ga": "Ga_d",
  "Gd": "Gd_3",
  "Ge": "Ge_d",
  "H": "H",
  "He": "He",
  "Hf": "Hf_pv",
  "Hg": "Hg",
  "Ho": "Ho_3",
  "I": "I",
  "In": "In_d",
  "Ir": "Ir",
  "K": "K_sv",
  "Kr": "Kr",
  "La": "La",
  "Li": "Li_sv",
  "Lu": "Lu_3",
  "Mg": "Mg",
  "Mn": "Mn_pv",
  "Mo": "Mo_sv",
  "N": "N",
  "Na": "Na_pv",
  "Nb": "Nb_sv",
  "Nd": "Nd_3",
  "Ne": "Ne",
  "Ni": "Ni",
  "Np": "Np",
  "O": "O",
  "Os": "Os",
  "P": "P",
  "Pa": "Pa",
  "Pb": "Pb_d",
  "Pd": "Pd",
  "Pm": "Pm_3",
  "Po": "Po_d",
  "Pr": "Pr_3",
  "Pt": "Pt",
  "Pu": "Pu",
  "Ra": "Ra_sv",
  "Rb": "Rb_sv",
  "Re": "Re",
  "Rh": "Rh_pv",
  "Rn": "Rn",
  "Ru": "Ru_pv",
  "S": "S",
  "Sb": "Sb",
  "Sc": "Sc_sv",
  "Se": "Se",
  "Si": "Si",
  "Sm": "Sm_3",
  "Sn": "Sn_d",
  "Sr": "Sr_sv",
  "Ta": "Ta_pv",
  "Tb": "Tb_3",
  "Tc": "Tc_pv",
  "Te": "Te",
  "Th": "Th",
  "Ti": "Ti_sv",
  "Tl": "Tl_d",
  "Tm": "Tm_3",
  "U": "U",
  "V": "V_sv",
  "W": "W_pv",
  "Xe": "Xe",
  "Y": "Y_sv",
  "Yb": "Yb_2",
  "Zn": "Zn",
  "Zr": "Zr_sv"
}
```



## regularize


* customized symbols
* numbers symbols
* charge
* spin
* comments
* atoms size




