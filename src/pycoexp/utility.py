import pandas as pd
import os


def iter_steadystates(self, foldername='updatedModels'):
    cpsmodels = [os.path.join(foldername, i) for i in os.listdir(foldername)]
    for i in range(len(cpsmodels)):
        dataModel = self.reinit_dataModel(cpsmodels[i])
        concentrations, fluxes = self.steadystate(dataModel=dataModel)
        colname = cpsmodels[i].split('\\')[1][:-4]
        if i == 0:
            Conc = pd.DataFrame.from_dict(concentrations, orient='index', columns=[colname, ])
            Fluxes = pd.DataFrame.from_dict(fluxes, orient='index', columns=[colname, ])
        else:
            Conc = Conc.join(pd.DataFrame.from_dict(concentrations, orient='index', columns=[colname, ]))
            Fluxes = Fluxes.join(pd.DataFrame.from_dict(fluxes, orient='index', columns=[colname, ]))
    return Conc, Fluxes


def rxn_edgeCases(rxn_name: str) -> str:
    rxns = {'WARS': 'WARS2_tRNA_recombinant_assume_km_equal_Ka_or_Kb',
            'TDO2': 'TDO', 'NADSYN1': 'NADS'}
    if rxn_name in rxns.keys():
        rxn_name = rxns[rxn_name]
    return rxn_name


def get_state(model):
    """
    returns dictionary of species concentration and reaction fluxes
    """
    Metabolite_Concentrations = {}
    for metab in model.getMetabolites():
        Metabolite_Concentrations['{}'.format(metab.getObjectDisplayName())] = metab.getConcentration()

    Reaction_Fluxes = {}
    for reaction in model.getReactions():
        Reaction_Fluxes['{}'.format(reaction.getObjectName())] = reaction.getFlux()
    return Metabolite_Concentrations, Reaction_Fluxes


def updateModel1(dataModel, parameter_name: str or list, value: float, E_T_or_k1: str, modelname: str):
    model = dataModel.getModel()
    if type(parameter_name) == list:
        for i in range(len(parameter_name)):
            updateParam(model=model, parameter_name=parameter_name[i], value=value[i], E_T_or_k1=E_T_or_k1)
    elif type(parameter_name) == str:
        updateParam(model=model, parameter_name=parameter_name, value=value, E_T_or_k1=E_T_or_k1)
    return dataModel.saveModel(modelname, True)


def updateParam(model, parameter_name: str, value: float, E_T_or_k1: str):
    try:
        mv = model.getModelValue(parameter_name)
        assert mv is not None, "Parameter {} not found".format(parameter_name)
        mv.setInitialValue(value)
    except AssertionError:
        rxn = model.getReaction(parameter_name)
        assert rxn is not None, "Reaction {} not found".format(parameter_name)
        para_value = rxn.getParameterValue(E_T_or_k1)
        assert para_value is not None, "No such parameter"
        rxn.setParameterValue(E_T_or_k1, value)
        assert rxn.getParameterValue(E_T_or_k1) == value


def updateModel(dataModel, parameter_name: str, value: float, E_T_or_k1: str, modelname: str):
    model = dataModel.getModel()
    try:
        mv = model.getModelValue(parameter_name)
        assert mv is not None, "Parameter {} not found".format(parameter_name)
        mv.setInitialValue(value)
    except AssertionError:
        rxn = model.getReaction(parameter_name)
        assert rxn is not None, "Reaction {} not found".format(parameter_name)
        para_value = rxn.getParameterValue(E_T_or_k1)
        assert para_value is not None, "No such parameter"
        rxn.setParameterValue(E_T_or_k1, value)
        assert rxn.getParameterValue(E_T_or_k1) == value
    return dataModel.saveModel(modelname, True)


def updateET(dataModel, parametertochange, expdata, mappingdata, datacolumn, foldername):
    model = dataModel.getModel()
    df = expdata
    reactions = df[df.columns[0]]
    count = 0
    for i in range(len(reactions)):
        # print(reactions[i])
        try:
            mv = model.getModelValue(reactions[i])
            assert mv is not None, "Parameter {} not found".format(reactions[i])
            mv.setInitialValue(df[df.columns[datacolumn]][i])
            assert mv.getInitialValue() == df[df.columns[datacolumn]][i]
            count += 1
        except AssertionError:
            try:
                rxn = model.getReaction(reactions[i])
                assert rxn is not None, "Reaction {} not found".format(reactions[i])
            except AssertionError:
                rxnID = mappingdata.loc[mappingdata.Model_ID == reactions[i], 'Name'].iloc[0]
                rxnID = rxn_edgeCases(rxnID)
                rxn = model.getReaction(rxnID)
                assert rxn is not None, "Reaction {} not found".format(rxnID)
            value = rxn.getParameterValue(parametertochange)
            assert value is not None, "No such parameter in {}".format(rxn.getObjectName())
            rxn.setParameterValue(parametertochange, df[df.columns[datacolumn]][i])
            assert rxn.getParameterValue(parametertochange) == df[df.columns[datacolumn]][i]
            count += 1
    assert count == len(df), "Successfully integrated {} of {} genes".format(count, len(df))
    modelname = foldername + df.columns[datacolumn].replace(' ', '_')+'.cps'
    return dataModel.saveModel(modelname, True)


def getparametervalue(dataModel, parameter_name, E_T_or_k1):
    model = dataModel.getModel()
    try:
        mv = model.getModelValue(parameter_name)
        assert mv is not None, "Parameter {} not found".format(parameter_name)
        pv = mv.getInitialValue()
    except AssertionError:
        rxn = model.getReaction(parameter_name)
        assert rxn is not None, "Reaction {} not found".format(parameter_name)
        pv = rxn.getParameterValue(E_T_or_k1)
        assert pv is not None, "No such parameter"
    return pv


def print_ReactionScheme(model):
    # output number and scheme of all reactions
    iMax = model.getNumReactions()
    print("Number of Reactions: ", iMax)
    print("Reactions: ")
    for i in range(0, iMax):
        reaction = model.getReaction(i)
        assert reaction is not None
        print("\t" + "{}: {}".format(reaction.getObjectName(), reaction.getReactionScheme()))
    # return [model.getReaction(i).getReactionScheme() for i in range(model.getNumReactions())]


def print_all_parameters(model, rxn_name='NUDT12'):
    """
    get names of all parameters of a reaction
    :param model: Cmodel object
    :param rxn_name: reaction name as string
    :return: list of strings parameter names
    """
    rxn = model.getReaction(rxn_name)
    params = rxn.getParameters()
    return [params.getName(i) for i in range(params.size())]


def print_compartments(model):
    # output number and names of all compartments
    iMax = model.getCompartments().size()
    print("Number of Compartments: ", iMax)
    print("Compartments: ")
    for i in range(0, iMax):
        compartment = model.getCompartment(i)
        assert compartment is not None
        print("\t" + compartment.getObjectName())


def print_metabolites(model):
    # output number and names of all metabolites
    iMax = model.getMetabolites().size()
    print("Number of Metabolites: ", iMax)
    print("Metabolites: ")
    for i in range(0, iMax):
        metab = model.getMetabolite(i)
        assert metab is not None
        print("\t" + metab.getObjectName())


def print_reactions(model):
    # output number and names of all reactions
    iMax = model.getReactions().size()
    print("Number of Reactions: ", iMax)
    print("Reactions: ")
    for i in range(0, iMax):
        reaction = model.getReaction(i)
        assert reaction is not None
        print("\t" + reaction.getObjectName())
