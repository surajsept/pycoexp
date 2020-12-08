# pycoexp
A python package that allows users to integrate expression data into Copasi (.cps) models. Additionally, it allows users to use copasi model and perform the following tasks: steadystate calculation, metabolic control analysis, and parameter scan.

The *pycoexp* framework is developed using Python 3.

****
#### 1. Getting python
You can download the latest version of Python [here](https://www.python.org/downloads/).
Alternatively, you can use [Anaconda](https://www.anaconda.com/download/) to install python for your computer (Linux, Windows, Mac).
  
#### 2. Installing packages using requirement file
      pip install -r requirements.txt

#### 3. Cloning and installing pycoexp pacakge
      git clone git@github.com:MolecularBioinformatics/pycoexp.git
      pip install -e pycoexp/ 

****
Once you have checked the steps above. You may consider refering to the [Beginners Guide](https://wiki.python.org/moin/BeginnersGuide). 
Or, just start a python console to: 
### Integrate expression values into a copasi model.

```python
import pycoexp.tasks
task = pycoexp.tasks.tasks()
# integrate expression values and save updated copasi models in folder 'updatedModels'
task.integrate_expression(filepath_CPSmodel='model.cps', filepath_expdata='ExpData.csv', filepath_mapping='mapping.csv',
                           foldername='updatedModels/', parametertochange='E_T')
```

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
ControlCoefficients, Elasticities = task.mca(filepath_CPSmodel='model.cps', system_variable='concentration')
```

### Example 3: To do a parameter scan
```python
# do parameter scan
Conc, Fluxes = task.scan(filepath_CPSmodel='model.cps', parameter_name='NAMPT', E_T_or_k1='E_T', lb=0.1, ub=1.0, n=10, rescaling=True)
```

****
*This is a development version, hosted as a private git repository, and people interested in contributing can request access by contacting Suraj Sharma (surajsept@gmail.com)*.
