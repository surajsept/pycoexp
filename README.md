# PyCoExp
A python package that allows users to integrate expression data into Copasi (.cps) models. Additionally, it allows users to use copasi model and perform the following tasks: steadystate calculation, metabolic control analysis, and parameter scan.

The *pycoexp* framework is developed using Python 3.

****
#### Cloning and installing pycoexp package
     $ pip install git+https://github.com/surajsept/pycoexp.git

****
Once you have checked the steps above. You may consider refering to the [Beginners Guide](https://wiki.python.org/moin/BeginnersGuide). 
Or, just start a python console to: 
### Integrate expression values into a copasi model.

```python
import pycoexp.tasks
task = pycoexp.tasks.tasks()
# integrate expression values and save updated copasi models in folder 'updatedModels'
task.integrate_expression(filepath_CPSmodel='model.cps', filepath_expdata='ExpData.csv', 
                          filepath_mapping='mapping.csv', foldername='updatedModels/')
```

#### File templates:
#### Mapping file template
|Name|Model_ID|...|
|---|---|---|
|   |   |   |
|   |   |   |

#### Expression file template
|Name|Exp1|Exp2|...|
|---|---|---|---|
|   |   |   |   |
|   |   |   |   |

here, "Name" corresponds to the gene name/symbol, "Model_ID" stands for the ID in SBML model and "Exp1..." stand for experiment/observation name.
****
Additionally,

### Example 1: To calculate steady state
```python
# get steady state
Concentration, Flux = task.steadystate(filepath_CPSmodel='model.cps')
```

### Example 2: To calculate control coefficients
```python
# perform metabolic control analysis
ControlCoefficients = task.mca(filepath_CPSmodel='model.cps', system_variable='concentration', verbose=True)
```

### Example 3: To do a parameter scan
```python
# do parameter scan
Conc, Fluxes = task.scan(filepath_CPSmodel='model.cps', parameter_name='NAMPT', E_T_or_k1='E_T', lb=0.1, ub=1.0, n=10, rescaling=True)
```

### Example 4: To do a time-course simulation
```python
# do time-course simulation
Conc, Fluxes = task.time_course(filepath_CPSmodel='model.cps', duration=100, stepsize=0.1)
```

****
*This is a development version, hosted as a private git repository, and people interested in contributing can request access by contacting Suraj Sharma (surajsept@gmail.com)*.
