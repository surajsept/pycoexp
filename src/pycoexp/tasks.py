import COPASI
import os
import shutil
import pandas as pd
import numpy as np

import pycoexp.MetabolicControlAnalysis
import pycoexp.utility as u

class tasks():
    def __init__(self):
        self.MCA = pycoexp.MetabolicControlAnalysis
        print(' ')

    def init_dataModel(self, filepath_CPSmodel: str):
        dataModel = COPASI.CRootContainer.addDatamodel()
        assert (isinstance(dataModel, COPASI.CDataModel))
        # load a Copasi model
        dataModel.loadModel(filepath_CPSmodel)
        return dataModel

    def mca(self, filepath_CPSmodel: str, system_variable: str):
        method = self.MCA.run_mca(file_name=filepath_CPSmodel)
        if system_variable == 'concentration':
            control_coeff = self.MCA.print_annotated_matrix("Scaled Concentration Control Coefficients", method.getScaledConcentrationCCAnn())
            elasticity = self.MCA.print_annotated_matrix("Scaled Elasticities", method.getScaledElasticitiesAnn())
            return control_coeff, elasticity
        elif system_variable == 'flux':
            control_coeff = self.MCA.print_annotated_matrix("Scaled Flux Control Coefficients", method.getScaledFluxCCAnn())
            elasticity = self.MCA.print_annotated_matrix("Scaled Elasticities", method.getScaledElasticitiesAnn())
            return control_coeff, elasticity
        else:
            return print("Use 'concentration' or 'flux' as system_variable")



    def scan(self, filepath_CPSmodel: str, parameter_name: str, E_T_or_k1: str, lb:float, ub:float, n:int,
             foldername='scan', deleteModels=False, rescaling=False):

        dataModel = self.init_dataModel(filepath_CPSmodel=filepath_CPSmodel)
        # create a folder to save CPS models
        os.makedirs(foldername, exist_ok=True)

        # creates a range of values
        vrange = np.linspace(lb, ub, n)

        # checks for rescaling the parameter value
        if rescaling is True:
            pv = u.getparametervalue(dataModel=dataModel, parameter_name=parameter_name, E_T_or_k1=E_T_or_k1)
            if pv != 0.0:
                vrange = pv * np.linspace(lb, ub, n)
            else:
                vrange = np.linspace(lb, ub, n)

        for i in range(len(vrange)):
            filepath_cpsmodel = os.path.join(foldername, parameter_name + '_' + str(vrange[i]) + '.cps')
            u.updateModel(dataModel=dataModel, parameter_name=parameter_name, value=vrange[i], E_T_or_k1=E_T_or_k1,
                          modelname=filepath_cpsmodel)
            concentrations, fluxes = self.steadystate(filepath_CPSmodel=filepath_CPSmodel)
            colname = vrange[i]
            if i == 0:
                Conc = pd.DataFrame.from_dict(concentrations, orient='index', columns=[colname,])
                Fluxes = pd.DataFrame.from_dict(fluxes, orient='index', columns=[colname,])
            else:
                Conc = Conc.join(pd.DataFrame.from_dict(concentrations, orient='index', columns=[colname,]))
                Fluxes = Fluxes.join(pd.DataFrame.from_dict(fluxes, orient='index', columns=[colname,]))
        if deleteModels==True:
            shutil.rmtree(foldername)
        return Conc, Fluxes

    def integrate_expression(self, filepath_CPSmodel: str, filepath_expdata: str, filepath_mapping: str,
                           foldername='updatedModels/', parametertochange='E_T'):
        dataModel = self.init_dataModel(filepath_CPSmodel=filepath_CPSmodel)
        expdata = pd.read_csv(filepath_expdata, delimiter='\t')
        mapping = pd.read_csv(filepath_mapping, delimiter='\t')
        if os.path.exists(foldername):
            shutil.rmtree(foldername)
        os.makedirs('updatedModels', exist_ok=True)
        for k in range(1, len(expdata.columns)):
            u.updateET(dataModel=dataModel, expdata=expdata, mappingdata=mapping, datacolumn=k,
                                      foldername=foldername, parametertochange=parametertochange)

    def steadystate(self, filepath_CPSmodel: str):
        '''
        Runs the model to steady state with the parameters as defined in the COPASI
        file (or default in case of SBML)
        :return: dictionaries of concentration of Metabolites and Reaction Fluxes
        '''
        dataModel = self.init_dataModel(filepath_CPSmodel=filepath_CPSmodel)

        # set the steady-state task
        task = dataModel.getTask('Steady-State')
        assert task != None

        # setup parameters as needed here ...
        task.initialize(COPASI.CCopasiTask.NO_OUTPUT)
        task.process(True)
        assert task.process(True) is True
        task.restore()
        Concentrations, Fluxes = u.get_state(dataModel.getModel())
        return Concentrations, Fluxes

    def modelSummary(self, filepath_CPSmodel: str):
        dataModel = self.init_dataModel(filepath_CPSmodel=filepath_CPSmodel)
        model = dataModel.getModel()
        iMax = model.getCompartments().size()
        print("Number of Compartments: ", iMax)
        iMax = model.getMetabolites().size()
        print("Number of Metabolites: ", iMax)
        iMax = model.getReactions().size()
        print("Number of Reactions: ", iMax)


########################################################################################################################

if __name__ == '__main__':
    task = tasks()
    dataModel = COPASI.CRootContainer.addDatamodel()
    assert (isinstance(dataModel, COPASI.CDataModel))
