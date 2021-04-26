# Isentropic Module
This module was developed by [ATA Engineering](http://www.ata-e.com) as an 
add-on to the Loci/CHEM computational fluid dynamics (CFD) solver. The 
module can be used to extend the **isentropicInflow** boundary condition to 
allow the user to specify a stagnation enthalpy instead of a stagnation
temperature. It also supports the **equilibrium** tag which will calculate
the equilibrium species mass fractions at the prescribed stagnation 
conditions.

# Dependencies
This module depends on both Loci and CHEM being installed. Loci is an open
source framework developed at Mississippi State University (MSU) by Dr. Ed 
Luke. The framework provides a rule-based programming model and can take 
advantage of massively parallel high performance computing systems. CHEM is 
a full featured open source CFD code with finite-rate chemistry built on 
the Loci framework. CHEM is export controlled under the International 
Traffic In Arms Regulations (ITAR). Both Loci and CHEM can be obtained from 
the [SimSys Software Forum](http://www.simcenter.msstate.edu) hosted by 
MSU. This module also requires a compiler with C++11 support.

# Installation Instructions
First Loci and CHEM should be installed. The **LOCI_BASE** environment
variable should be set to point to the Loci installation directory. The 
**CHEM_BASE** environment variable should be set to point to the CHEM 
installation directory. The installation process follows the standard 
make, make install procedure.

```bash
make
make install
```

# Usage
First the module must be loaded at the top of the **vars** file. 
Any **isentropicInflow** boundaries conditions may be tagged with the 
**h0** and/or **equilibrium** tags. 

```
loadModule: isentropic

boundary_conditions: <BC_1=isentropicInflow(p0=53e6 Pa, h0=9.1e6 J/kg, 
                                            mixture=[N2=1.0, N=0.0], 
                                            equilibrium), ...>
```
