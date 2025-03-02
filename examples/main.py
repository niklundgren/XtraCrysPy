from XtraCrysPy import Atomic as XCP
from sys import argv

if '__main__' == __name__:

  argc = len(argv)
  if argc < 2 or argv[1] == '-h':
    print('Usage:')
    print('  python main.py <inputfile>')
    print('  python main.py <inputfile> <bond_length>\n')
    print('Control Inputs:')
    print('  \'u\' : Toggle UI visibility')
    print('  \'a\' : Toggle Axis visibility')
    print('  \'b\' : Toggle Boundary visiblity')
    print('  \'c\' : Toggle constraint of atoms within cell')
    print('  \'>\' : Step forward in relax or MD')
    print('  \'<\' : Step backward in relax or MD')
    print('  CTRL + (\'>\' or \'<\') : Step 5% through the relaxation or MD steps')
    print('  SHIFT + \'s\' : Take snapshot')
    print('  CTRL + \'w\' : Exit')
    print('  Arrow Keys : Rotate model')
    print('  SHIFT + Arrow Keys : Translate camera')
    print('  CTRL + Arrow Keys (+ SHIFT) : Rotate (or Translate) in smaller steps')
    exit()

  a_info = {}
  if argc > 2:
    # Bond length in Bohr
    a_info['bonds'] = float(argv[2])

  fname = argv[1]
  xcp = XCP.Atomic(params=a_info, model=fname, sel_type='Chain')
  xcp.start_crystal_view()

