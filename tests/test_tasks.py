import unittest
import pycoexp.tasks
import COPASI
import pandas

task = pycoexp.tasks.tasks()

class MyTestCase(unittest.TestCase):
    def test_init_dataModel(self):
        dm = task.init_dataModel('../src/pycoexp/model.cps')
        self.assertTrue(isinstance(dm, COPASI.CDataModel))

    def test_steadystate(self):
        result = task.steadystate('../src/pycoexp/model.cps')
        self.assertEqual(len(result), 2)
        self.assertIs(type(result[0]), dict)
        self.assertIs(type(result[1]), dict)

    def test_time_course(self):
        result = task.time_course(filepath_CPSmodel='../src/pycoexp/model.cps', duration=10, intervals=10)
        self.assertIs(type(result), pandas.DataFrame)
        self.assertEqual(len(result), 11)

    def test_scan(self):
        result = task.scan(filepath_CPSmodel='../src/pycoexp/model.cps', parameter_name='NAMPT', E_T_or_k1='E_T',
                           lb=0.1, ub=1.0, n=10, rescaling=True, deleteModels=True)
        self.assertEqual(len(result), 2)
        self.assertIs(type(result[0]), pandas.DataFrame)
        self.assertIs(type(result[1]), pandas.DataFrame)

    def test_integrate_expression(self):
        result = task.integrate_expression(filepath_CPSmodel='../src/pycoexp/model.cps',
                                           filepath_expdata='../src/pycoexp/ExpData.csv',
                                           filepath_mapping='../src/pycoexp/mapping.csv',
                                           foldername='../src/pycoexp/updatedModels/', parametertochange='E_T')
        self.assertEqual(result, 0)

    def test_mca(self):
        result = task.mca(filepath_CPSmodel='../src/pycoexp/model.cps', system_variable='concentration', verbose=False)
        self.assertIs(type(result), pandas.DataFrame)





if __name__ == '__main__':
    unittest.main()
