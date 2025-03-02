import numpy as np

class Model:

  def __init__ ( self, params=None, fname=None, multi_frame=False, ftype=None, index=None ):
    '''

    Arguments:
    '''
    from .defaults import atom_defaults
    from .conversion import ANG_BOHR

    if params is None:
      params = {}

    self.species = None
    self.lunit = 'angstrom'
    self.aunit = 'angstrom'
    self.bunit = 'angstrom'
    self.relax = multi_frame
    if fname is not None:
      self.lunit = 'bohr'
      self.aunit = 'crystal'
      if self.relax:
        if isinstance(fname, list):
          from .file_io import struct_from_file_sequence
          params.update(struct_from_file_sequence(fname, ftype=ftype))
        else:
          from .file_io import struct_from_inputfile
          if ftype is None or ftype == 'espresso-in':
            ftype = 'espresso-out'
          params.update(struct_from_inputfile(fname, ftype=ftype, index=slice(0,-1)))
      else:
        from .file_io import struct_from_inputfile
        if ftype == 'lammps-traj':
          self.relax = True
        params.update(struct_from_inputfile(fname, ftype=ftype, index=index))

    try:
      self.bond_type = None
      if 'abc' in params:
        self.atoms = params['abc']
      else:
        self.atoms = np.array([], dtype=float)
      if 'lattice' in params:
        self.lattice = params['lattice']
      else:
        self.lattice = np.eye(3, dtype=float)
      if 'species' in params:
        self.species = params['species']
    except:
      raise Exception('Manual structures require \'lattice\', \'species\', and atomic positions \'abc\'')

    if self.relax and len(self.lattice.shape) == 2:
      self.lattice = np.array([self.lattice])

    if 'lunit' in params:
      self.lunit = params['lunit']
    if 'aunit' in params:
      self.aunit = params['aunit']
    if 'bunit' in params:
      self.bunit = params['bunit']

    ati = 0 if not self.relax else 1
    if self.species is None:
      self.species = [str(s) for s in range(self.atoms.shape[ati])]

    self.natoms = len(self.species)
    shape = self.atoms.shape[ati]
    if self.natoms != shape:
      raise ValueError('Number of atoms and species do not match')

    if not self.relax:
      self.volume = self.lattice[0].dot(np.cross(self.lattice[1], self.lattice[2]))

      self.rlattice = np.empty_like(self.lattice)
      for i in range(3):
        self.rlattice[i,:] = np.cross(self.lattice[i-2], self.lattice[i-1])
      self.rlattice *= 2 * np.pi / self.volume

    self.bonds = {}
    self.bond_thickness = 1
    if 'bonds' in params:
      bval = params['bonds']
      if not isinstance(bval, (int,float,dict)):
        raise TypeError('bonds value in params dictionary must be either a dictionary or number')
      if isinstance(bval, dict):
        bval = bval.copy()
        if 'thickness' in bval:
          self.bond_thickness = bval['thickness']
          del bval['thickness']
        if 'distance' in bval:
          bval = bval['distance']
        else:
          for k,v in bval.items():
            key = k
            if '_' not in key:
              key = '{}_{}'.format(key, key)
            self.bonds[key] = v
      if isinstance(bval, (int,float)):
        bonds = {}
        uspec = list(set(self.species))
        nuat = len(uspec)
        for s in uspec:
          bonds['{}_{}'.format(s,s)] = bval
        for i,s1 in enumerate(uspec[:-1]):
          for j in range(i+1, nuat):
            s2 = uspec[j]
            bonds['{}_{}'.format(s1,s2)] = bval
        self.bonds = bonds

    self.colors = {}
    if 'colors' in params:
      for k,v in params['colors'].items():
        self.colors[k] = np.array(v)

    self.radii = {}
    if 'radii' in params:
      radii = params['radii']
      if isinstance(radii, (int,float)):
        for s in self.species:
          self.radii[s] = radii
      elif isinstance(radii, dict):
        for k,v in params['radii'].items():
          self.radii[k] = v

    if self.lunit == 'bohr':
      pass
    elif self.lunit == 'angstrom':
      self.lattice *= ANG_BOHR

    if self.aunit in ['scaled', 'crystal']:
      pass
    else:
      if self.aunit == 'angstrom':
        self.atoms *= ANG_BOHR
      elif self.aunit != 'bohr':
        raise Exception(f'Unit {self.aunit} is unsupported.')
      linv = np.linalg.inv(self.lattice)
      for i,p in enumerate(self.atoms):
        self.atoms[i] = p @ linv

    if self.bunit == 'angstrom':
      for k in self.bonds.keys():
        self.bonds[k] *= ANG_BOHR

    for s in self.species:
      if not s in self.colors:
        if s in atom_defaults:
          self.colors[s] = np.array(atom_defaults[s]['color'])/255
        else:
          self.colors[s] = (.8,.8,.8)
      if s not in self.radii:
        if s in atom_defaults:
          self.radii[s] = atom_defaults[s]['radius']
        else:
          self.radii[s] = 1

    if len(self.radii.keys()) > 0:
      self.primary_radius = np.min([r for k,r in self.radii.items()])
    else:
      self.primary_radius = 1


  def constrain_atoms_to_unit_cell ( self, lattice, atoms ):
    '''
    Force atoms to lie inside of the unit cell.

    Arguments:
      lattice (ndarray): 3x3 array of lattice vectors
      atoms (list): List of 3 component vectors representing the atomic basis

    Returns:
      (list): Updated list of atomic positions
    '''
    def inside_cell ( apos ):
      for v in apos:
        if v > 1 or v < 0:
          return False
      return True

    for i,a in enumerate(atoms):
      while not inside_cell(atoms[i]):
        for j,n in enumerate(atoms[i]):
          if n < 0:
            atoms[i][j] += 1
          elif n >= 1:
            atoms[i][j] -= 1

    return atoms


  def bond_radius ( self, dist, aind1, aind2, bond_type ):
    brad = .1
    if bond_type == 'Stick':
      brad = .5 / dist
    elif bond_type == 'Primary':
      brad = 1.5 * self.primary_radius / dist
    elif bond_type != 'Sphere':
      raise ValueError('Bond types are Stick, Primary, and Sphere')
    s1 = self.species[aind1%self.natoms]
    s2 = self.species[aind2%self.natoms]
    bspec = 1.8 / dist * np.min([self.radii[s1], self.radii[s2]])
    return np.min([self.bond_thickness*brad, bspec])


  def lattice_atoms_bonds ( self, nc1, nc2, nc3, bond_type='stick', frame_index=0, constrain_atoms=True ):
    '''
    '''

    oatoms = self.atoms.copy() if not self.relax else self.atoms[frame_index].copy()

    lattice = self.lattice
    if self.relax:
      ind = frame_index if lattice.shape[0]==self.atoms.shape[0] else 0
      lattice = lattice[ind]
    lattice = lattice.copy()

    if constrain_atoms:
      oatoms = self.constrain_atoms_to_unit_cell(lattice, oatoms)

    nsc = (nc1,nc2,nc3)
    nat = oatoms.shape[0]

    if self.bond_type is None:
      self.bond_type = bond_type

    frame = []
    lat = lattice
    for ix in range(nc1):
      for iy in range(nc2):
        for iz in range(nc3):
          orig = np.array([ix,iy,iz]) @ lat
          corner = np.sum(lat, axis=0) + orig
          frame += [[orig,orig+a] for a in lat]
          frame += [[orig+p,corner] for p in [lat[i]+lat[j] for i in range(3) for j in range(i+1,3)]]
          frame += [[orig+lat[k],orig+lat[i]+lat[j]] for i in range(3) for j in range(i+1,3) for k in [i,j]]
    frame = np.array(frame)

    bpoints = np.empty((2,6,3), dtype=float)
    bp = np.array([nsc[i]*lattice[i] for i in range(3)])
    for i in range(3):
      bpoints[0,i] = (bp[i-2] + bp[i-1])/2
      bpoints[1,i] = np.cross(bp[i-1], bp[i-2])
      bpoints[0,i+3] = bpoints[0,i] + bp[i]
      bpoints[1,i+3] = -bpoints[1,i]

    for i,n in enumerate(nsc):
      lattice[i,:] *= n

    atoms = []
    acols = []
    radii = []
    for n1 in range(nc1):
      for n2 in range(nc2):
        for n3 in range(nc3):
          origin = np.array([n1,n2,n3])
          for i,a in enumerate(oatoms):
            spec = self.species[i]
            atoms.append(origin + a)
            radii.append(self.radii[spec])
            acols.append(self.colors[spec])
    atoms = np.array(atoms)
    acols = np.array(acols)
    radii = np.array(radii)

    if atoms.shape[0] != 0:
      for i,n in enumerate(nsc):
        atoms[:,i] /= n
      atoms = atoms @ lattice

    bonds = []
    bdirs = []
    bcols = []
    brads = []
    bheight = []
    natsc = atoms.shape[0]
    skey = lambda v1,v2 : f'{v1}_{v2}'
    if bond_type == 'Sphere':
      dist_min = 1e5
      for i1 in range(natsc-1):
        for i2 in range(i1+1, natsc):
          dist = np.linalg.norm(atoms[i2]-atoms[i1])
          if dist < dist_min:
            dist_min = dist
      radii *= 1.3 * dist_min
    elif len(self.bonds.keys()) > 0:
      if frame_index == 0 and natsc > 500:
        print('WARNING: Large number of atoms.')
        print('         Unset bonds to improve performance.')
      for i1 in range(natsc-1):
        for i2 in range(i1+1, natsc):
          a1 = atoms[i1]
          a2 = atoms[i2]
          t1 = self.species[i1%nat]
          t2 = self.species[i2%nat]

          bnd_len = None
          if skey(t1,t2) in self.bonds:
            bnd_len = self.bonds[skey(t1,t2)]
          elif skey(t2,t1) in self.bonds:
            bnd_len = self.bonds[skey(t2,t1)]
        
          if not bnd_len is None:
            conn = a2 - a1
            dist = np.linalg.norm(conn)
            if bnd_len >= dist:
              cent = (a1 + a2) / 2
              bonds.append([cent-conn/4, cent+conn/4])
              bdir = conn/dist
              bdirs.append([bdir]*2)
              bcols.append([self.colors[t1], self.colors[t2]])
              brads.append(self.bond_radius(dist,i1,i2,self.bond_type))
              bheight.append(dist/2)

    bonds = np.array(bonds)
    bdirs = np.array(bdirs)
    bcols = np.array(bcols)
    brads = np.array(brads)
    bheight = np.array(bheight)

    return (atoms,acols,radii), (bonds,bdirs,bcols,brads,bheight), (bpoints,frame)
