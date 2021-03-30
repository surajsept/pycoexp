import COPASI
import os
import shutil
import pandas as pd
import numpy as np
import logging

import pycoexp.MetabolicControlAnalysis
import pycoexp.utility

class tasks():
    def __init__(self):
        self.MCA = pycoexp.MetabolicControlAnalysis
        self.util = pycoexp.utility

    def optimization(self, filepath_CPSmodel: str, **kwargs):
        '''
        performs optimization
        :param filepath_CPSmodel: path to model (.cps) as str
        :return tuple: objective value (float), optimized values (list of float)
        '''
        # create dataModel object
        dataModel = self.init_dataModel(filepath_CPSmodel=filepath_CPSmodel)

        # create optimization task
        optTask = dataModel.getTask("Optimization")

        if 'method' in kwargs:
            optTask.setMethodType(kwargs['method'])
            optMethod = optTask.getMethod()
            assert optMethod is not None

        if 'parameter' in kwargs:
            if type(kwargs['parameter']) is list:
                assert len(kwargs['parameter']) == len(kwargs['parameter_value'])
                for i in range(len(kwargs['parameter'])):
                    parameter = optMethod.getParameter(kwargs['parameter'][i])
                    assert parameter is not None
                    parameter.setIntValue(kwargs['parameter_value'][i])
            else:
                parameter = optMethod.getParameter(kwargs['parameter'])
                assert parameter is not None
                parameter.setIntValue(kwargs['parameter_value'])

        # # we want to use Levenberg-Marquardt as the optimization method
        # optTask.setMethodType(COPASI.CTaskEnum.Method_LevenbergMarquardt)
        # optMethod = optTask.getMethod()
        # assert optMethod != None
        # # now we set some method parameters for the optimization method
        # # iteration limit
        # parameter = optMethod.getParameter("Iteration Limit")
        # assert parameter != None
        # parameter.setIntValue(2000)
        # # tolerance
        # parameter = optMethod.getParameter("Tolerance")
        # assert parameter != None
        # parameter.setDblValue(1.0e-5)

        optProblem = optTask.getProblem()

        # set process to True
        optTask.process(True)

        result = [optProblem.getSolutionVariables().get(j) for j in range(optProblem.getSolutionVariables().size())]
        objectiveValue = optProblem.getSolutionValue()
        return objectiveValue, result


    def init_dataModel(self, filepath_CPSmodel: str):
        '''
        returns an instance of model
        :param filepath_CPSmodel: path to model (.cps) as str
        :return COPASI.CDataModel instance
        '''
        dataModel = COPASI.CRootContainer.addDatamodel()
        assert (isinstance(dataModel, COPASI.CDataModel))
        # load a Copasi model
        dataModel.loadModel(filepath_CPSmodel)
        return dataModel


    def mca(self, filepath_CPSmodel: str, system_variable: str, verbose:bool):
        '''
        runs metabolic control analysis
        :param filepath_CPSmodel: str; path to model (.cps)
        :param system_variable: str; Possible inputs for system_variable: concentration, flux, elasticity
        :return pandas.Dataframe: coefficients
        '''
        method = self.MCA.run_mca(file_name=filepath_CPSmodel)

        assert system_variable in ['concentration', 'flux', 'elasticity'], \
            'Possible inputs for system_variable: concentration, flux, elasticity'

        if system_variable == 'concentration':
            control_coeff = self.MCA.print_annotated_matrix("Scaled Concentration Control Coefficients",
                                                       method.getScaledConcentrationCCAnn(), verbose)
            return control_coeff
        elif system_variable == 'flux':
            control_coeff = self.MCA.print_annotated_matrix("Scaled Flux Control Coefficients",
                                                            method.getScaledFluxCCAnn(), verbose)
            return control_coeff
        elif system_variable == 'elasticity':
            elasticity = self.MCA.print_annotated_matrix("Scaled Elasticities", method.getScaledElasticitiesAnn(),
                                                         verbose)
            return elasticity


    def scan(self, filepath_CPSmodel: str, parameter_name: str, E_T_or_k1='k1', **kwargs):
        """
        performs a scan of parameter values
        :param filepath_CPSmodel: path to model (.cps)
        :type filepath_CPSmodel: str
        :param parameter_name: name of the parameter
        :type parameter_name: str
        :param E_T_or_k1: E_T or k1 (rate constant)
        :type E_T_or_k1: str
        :param kwargs:
        :type kwargs:
        :return: steady-state concentraions and fluxes for different parameter value
        :rtype: tuple
        """

        dataModel = self.init_dataModel(filepath_CPSmodel=filepath_CPSmodel)

        # create a folder to save CPS models
        foldername = kwargs.get('foldername', 'scan')
        os.makedirs(foldername, exist_ok=True)

        # creates a range of values
        lb = kwargs.get('lb', 1.0)
        ub = kwargs.get('ub', 10.0)
        n = kwargs.get('n', 10)

        vrange = np.linspace(lb, ub, n)

        # checks for rescaling the parameter value
        if 'rescaling' in kwargs and kwargs['rescaling'] is True:
            pv = self.util.getparametervalue(dataModel=dataModel, parameter_name=parameter_name, E_T_or_k1=E_T_or_k1)
            if pv != 0.0:
                vrange = pv * np.linspace(lb, ub, n)
            else:
                print("Initial value of {} is 0.0".format(pv))


        for i in range(len(vrange)):
            filepath_cpsmodel = os.path.join(foldername, parameter_name + '_' + str(vrange[i]) + '.cps')
            self.util.updateModel(dataModel=dataModel, parameter_name=parameter_name, value=vrange[i],
                                  E_T_or_k1=E_T_or_k1, modelname=filepath_cpsmodel)
            concentrations, fluxes = self.steadystate(filepath_CPSmodel=filepath_CPSmodel)
            colname = vrange[i]
            concentrations = pd.DataFrame.from_dict(concentrations, orient='index', columns=[colname, ])
            fluxes = pd.DataFrame.from_dict(fluxes, orient='index', columns=[colname, ])
            if i == 0:
                Conc = concentrations
                Fluxes = fluxes
            else:
                Conc = Conc.join(concentrations)
                Fluxes = Fluxes.join(fluxes)

        if 'deleteModels' in kwargs and kwargs['deleteModels'] is True:
            shutil.rmtree(foldername)
        return Conc, Fluxes


    def integrate_expression(self, filepath_CPSmodel: str, filepath_expdata: str, filepath_mapping: str,
                             foldername='updatedModels/', parametertochange='E_T'):
        '''
        integrates expression data as ET in the model
        :param filepath_CPSmodel: path to model (.cps) for data integration
        :type filepath_CPSmodel: str
        :param filepath_expdata: path to expression data
        :type filepath_expdata: str
        :param filepath_mapping: path to mapping file
        :type filepath_mapping: str
        :param foldername: path to folder where model(s) after data integration can be stored; default is 'updatedModels/'
        :type foldername: str
        :param parametertochange: specification of parameter; default is 'E_T'
        :type parametertochange: str
        :return: success 0; no success 1
        :rtype: int
        '''
        dataModel = self.init_dataModel(filepath_CPSmodel=filepath_CPSmodel)
        expdata = pd.read_csv(filepath_expdata, delimiter='\t')
        mapping = pd.read_csv(filepath_mapping, delimiter='\t')
        if os.path.exists(foldername):
            shutil.rmtree(foldername)
        os.makedirs(foldername, exist_ok=True)
        for k in range(1, len(expdata.columns)):
            self.util.updateET(dataModel=dataModel, expdata=expdata, mappingdata=mapping, datacolumn=k,
                               foldername=foldername, parametertochange=parametertochange)
        if len(os.listdir(foldername)) == len(expdata.columns)-1:
            return 0
        else:
            return 1


    def steadystate(self, filepath_CPSmodel: str, **kwargs):
        '''

        :param filepath_CPSmodel: path to model (.cps)
        :type filepath_CPSmodel: str
        :param kwargs: 'scheduled', 'update_model'
        :type kwargs: bool, bool
        :return: dictionary of steady-state concentrations and fluxes
        :rtype: tuple
        '''
        """
        Runs the model to steady state with the parameters as defined in the COPASI
        file (or default in case of SBML)
        :return: dictionaries of concentration of Metabolites and Reaction Fluxes
        """
        dataModel = self.init_dataModel(filepath_CPSmodel=filepath_CPSmodel)

        # set the steady-state task
        task = dataModel.getTask('Steady-State')
        assert (isinstance(task, COPASI.CSteadyStateTask))

        if 'scheduled' in kwargs:
            task.setScheduled(kwargs['scheduled'])

        if 'update_model' in kwargs:
            task.setUpdateModel(kwargs['update_model'])

        # problem = task.getProblem()
        # assert (isinstance(problem, COPASI.CSteadyStateProblem))

        task.initialize(COPASI.CCopasiTask.NO_OUTPUT)

        task.process(True)
        assert task.process(True) is True

        state = task.getResult()
        assert (state == 1)
        # task.restore()
        Concentrations, Fluxes = self.util.get_state(dataModel.getModel())
        return Concentrations, Fluxes


    def modelSummary(self, filepath_CPSmodel: str):
        '''
        prints model summary
        :param filepath_CPSmodel: path to model (.cps)
        :type filepath_CPSmodel: str
        :return: prints "Number of Compartments", "Number of Metabolites", "Number of Reactions"
        :rtype: str
        '''
        dataModel = self.init_dataModel(filepath_CPSmodel=filepath_CPSmodel)
        model = dataModel.getModel()
        iMax = model.getCompartments().size()
        print("Number of Compartments: ", iMax)
        iMax = model.getMetabolites().size()
        print("Number of Metabolites: ", iMax)
        iMax = model.getReactions().size()
        print("Number of Reactions: ", iMax)


    def time_course(self, filepath_CPSmodel: str, *args, **kwargs):
        '''
        runs time course simulation
        :param filepath_CPSmodel:
        :type filepath_CPSmodel:
        :param args:
        :type args:
        :param kwargs: 'scheduled', 'update_model', 'method', 'duration', 'automatic', 'output_event', 'start_time',
                        'start_time', 'step_number', 'intervals', 'stepsize', 'seed', 'use_seed', 'a_tol', 'r_tol',
                        'max_steps', 'use_numbers'
        :type kwargs: bool, bool, str, float, bool,
        :return:
        :rtype:
        '''
        model = self.init_dataModel(filepath_CPSmodel=filepath_CPSmodel)
        num_args = len(args)
        use_initial_values = kwargs.get('use_initial_values', True)

        task = model.getTask('Time-Course')
        assert (isinstance(task, COPASI.CTrajectoryTask))

        if 'scheduled' in kwargs:
            task.setScheduled(kwargs['scheduled'])

        if 'update_model' in kwargs:
            task.setUpdateModel(kwargs['update_model'])

        if 'method' in kwargs:
            task.setMethodType(self.__method_name_to_type(kwargs['method']))

        problem = task.getProblem()
        assert (isinstance(problem, COPASI.CTrajectoryProblem))

        if 'duration' in kwargs:
            problem.setDuration(kwargs['duration'])

        if 'automatic' in kwargs:
            problem.setAutomaticStepSize(kwargs['automatic'])

        if 'output_event' in kwargs:
            problem.setOutputEvent(kwargs['output_event'])

        if 'start_time' in kwargs:
            problem.setOutputStartTime(kwargs['start_time'])

        if 'step_number' in kwargs:
            problem.setStepNumber(kwargs['step_number'])

        if 'intervals' in kwargs:
            problem.setStepNumber(kwargs['intervals'])

        if 'stepsize' in kwargs:
            problem.setStepSize(kwargs['stepsize'])

        if num_args == 3:
            problem.setOutputStartTime(args[0])
            problem.setDuration(args[1])
            problem.setStepNumber(args[2])
        elif num_args == 2:
            problem.setDuration(args[0])
            problem.setStepNumber(args[1])
        elif num_args > 0:
            problem.setDuration(args[0])

        problem.setTimeSeriesRequested(True)

        method = task.getMethod()
        if 'seed' in kwargs and method.getParameter('Random Seed'):
            method.getParameter('Random Seed').setIntValue(int(kwargs['seed']))
        if 'use_seed' in kwargs and method.getParameter('Random Seed'):
            method.getParameter('Use Random Seed').setBoolValue(bool(kwargs['use_seed']))
        if 'a_tol' in kwargs and method.getParameter('Absolute Tolerance'):
            method.getParameter('Absolute Tolerance').setDblValue(float(kwargs['a_tol']))
        if 'r_tol' in kwargs and method.getParameter('Relative Tolerance'):
            method.getParameter('Relative Tolerance').setDblValue(float(kwargs['r_tol']))
        if 'max_steps' in kwargs and method.getParameter('Max Internal Steps'):
            method.getParameter('Max Internal Steps').setIntValue(int(kwargs['max_steps']))

        result = task.initializeRaw(COPASI.CCopasiTask.ONLY_TIME_SERIES)
        if not result:
            logging.error("Error while initializing the simulation: " +
                          COPASI.CCopasiMessage.getLastMessage().getText())
        else:
            result = task.processRaw(use_initial_values)
            if not result:
                logging.error("Error while running the simulation: " +
                              COPASI.CCopasiMessage.getLastMessage().getText())

        use_concentrations = kwargs.get('use_concentrations', True)
        if 'use_numbers' in kwargs and kwargs['use_numbers']:
            use_concentrations = False

        return self.__build_result_from_ts(task.getTimeSeries(), use_concentrations)

    ########################################################################################################################


    def __method_name_to_type(self, method_name):
        methods = {
            'deterministic': COPASI.CTaskEnum.Method_deterministic,
            'lsoda': COPASI.CTaskEnum.Method_deterministic,
            'hybridode45': COPASI.CTaskEnum.Method_hybridODE45,
            'hybridlsoda': COPASI.CTaskEnum.Method_hybridLSODA,
            'adaptivesa': COPASI.CTaskEnum.Method_adaptiveSA,
            'tauleap': COPASI.CTaskEnum.Method_tauLeap,
            'stochastic': COPASI.CTaskEnum.Method_stochastic,
            'directMethod': COPASI.CTaskEnum.Method_directMethod,
            'radau5': COPASI.CTaskEnum.Method_RADAU5,
            'sde': COPASI.CTaskEnum.Method_stochasticRunkeKuttaRI5,
        }
        return methods.get(method_name.lower(), COPASI.CTaskEnum.Method_deterministic)


    def __build_result_from_ts(self, time_series, use_concentrations=True):
        col_count = time_series.getNumVariables()
        row_count = time_series.getRecordedSteps()

        column_names = []
        column_keys = []
        for i in range(col_count):
            column_keys.append(time_series.getKey(i))
            column_names.append(time_series.getTitle(i))

        concentrations = np.empty([row_count, col_count])
        for i in range(row_count):
            for j in range(col_count):
                if use_concentrations:
                    concentrations[i, j] = time_series.getConcentrationData(i, j)
                else:
                    concentrations[i, j] = time_series.getData(i, j)

        df = pd.DataFrame(data=concentrations, columns=column_names)
        df = df.set_index('Time')
        return df

if __name__ == '__main__':
    task = tasks()

