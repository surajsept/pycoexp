from COPASI import *
import pandas as pd
import numpy as np

dataModel = None


def print_annotated_matrix(title: str, annotated_matrix: FloatMatrix) -> pd.DataFrame:
	"""
	Utility function printing an annotated matrix
	"""

	# print(annotated_matrix.printToString())
	# return

	print(title)
	print('==========')

	size = annotated_matrix.size()
	if len(size) != 2:
		print(" This simple function only deals with two dimensional matrices")
		return

	rows = size[0]
	columns = size[1]
	print("Size of the matrix is: {0} rows x {1} columns".format(rows, columns))

	row_headers = annotated_matrix.getAnnotationsString(0)
	col_headers = annotated_matrix.getAnnotationsString(1)

	df = pd.DataFrame(np.zeros((rows, columns)), columns=[i for i in col_headers], index=[i for i in row_headers])
	for i in range(0, rows):
		for j in range(0, columns):
			df.iloc[i, j] = annotated_matrix.array().get(j, i)
	return df


def run_mca(file_name: str) -> CMCAMethod:
	"""
	This function runs the MCA task on the given Copasi/SBML file
	"""

	global dataModel
	if dataModel is None:
		dataModel = CRootContainer.addDatamodel()
		assert (isinstance(dataModel, CDataModel))

	# load COPASI file
	try:
		if file_name.endswith('.cps'):
			if not dataModel.loadModel(file_name):
				print("Could not load COPASI file due to:")
				print(CCopasiMessage.getAllMessageText())
				sys.exit(1)
		# load sbml file
		elif not dataModel.importSBML(file_name):
			print("Could not load SBML file due to:")
			print(CCopasiMessage.getAllMessageText())
			sys.exit(1)
	except:
		print("Could not load file due to:")
		print(CCopasiMessage.getAllMessageText())
		sys.exit(1)

	# setup mca task
	task = dataModel.getTask("Metabolic Control Analysis")
	assert (isinstance(task, CMCATask))
	# mark task as executable
	task.setScheduled(True)
	problem = task.getProblem()
	assert (isinstance(problem, CMCAProblem))
	# specify that we want to perform steady state analysis
	problem.setSteadyStateRequested(True)

	# run mca task
	if not task.initialize(CCopasiTask.OUTPUT_UI):
		print("could not initialize mca task")
		print(CCopasiMessage.getAllMessageText())
		sys.exit(2)

	if not task.processWithOutputFlags(True, CCopasiTask.OUTPUT_UI):
		print("could not run mca task")
		print(task.getProcessError())
		sys.exit(3)

	# print results
	method = task.getMethod()
	assert (isinstance(method, CMCAMethod))
	return method
