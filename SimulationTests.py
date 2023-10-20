import discover
import unittest
import picause


class TestPicause(unittest.TestCase):
    def setUp(self):
        self.seed = 977351692186939434046756
        self.graphstr = "050409;06020508;010704;090A;070A;0308;"

    def test_graphstr2pairlist(self):
        pl = picause.adjacencystr2pairlist(self.graphstr)
        self.assertEqual(len(pl), 10)
        self.assertTrue(('x_6', 'x_5') in pl)
        self.assertTrue(('x_1', 'x_7') in pl)

    def test_oriented_confusion_matrix_defences(self):
        with self.assertRaises(ValueError):
            picause.oriented_confusion_matrix(None, "")
            picause.oriented_confusion_matrix("A --> B", None)
            picause.oriented_confusion_matrix("abcd", "")
            picause.oriented_confusion_matrix("", "abcd")
            picause.oriented_confusion_matrix("A --> B", "A --- B", "foo")

        result = picause.oriented_confusion_matrix("A --> B", "")
        self.assertEqual(result['oriented_FN'], 0)
        self.assertEqual(result['oriented_FP'], 0)
        self.assertEqual(result['oriented_TP'], 0)

    def test_oriented_confusion_matrix_results(self):
        tg1 = "A --> B, C --> B, C --> D"
        dg1 = "A --> B, C --> B, C --- D"
        result1_1 = picause.oriented_confusion_matrix(tg1, dg1, "edges")
        result1_2 = picause.oriented_confusion_matrix(tg1, dg1, "dict")
        self.assertTrue(('A', 'B') in result1_1['TP'])
        self.assertTrue(('C', 'B') in result1_1['TP'])
        self.assertTrue(('C', 'D') in result1_1['FN'])
        self.assertEqual(result1_2['oriented_TP'], 2)
        self.assertEqual(result1_2['oriented_FN'], 1)
        self.assertEqual(result1_2['oriented_FP'], 0)

        tg2 = "A --> B, A --> C"
        dg2 = "B --> A, A --- C"
        result2_1 = picause.oriented_confusion_matrix(tg2, dg2, "edges")
        result2_2 = picause.oriented_confusion_matrix(tg2, dg2, "dict")
        self.assertTrue(('A', 'B') in result2_1['FN'])
        self.assertEqual(result2_2['oriented_TP'], 0)
        self.assertEqual(result2_2['oriented_FN'], 2)
        self.assertEqual(result2_2['oriented_FP'], 1)

        tg3 = "A --> B, B --> C, D --> B, B --> E, D --> F, E --> F"
        dg3 = "A --> B, D --> B, B --> E, D --- E, D --- F, E --- F"
        result3_1 = picause.oriented_confusion_matrix(tg3, dg3, "edges")
        result3_2 = picause.oriented_confusion_matrix(tg3, dg3, "dict")
        self.assertTrue(('A', 'B') in result3_1['TP'])
        self.assertEqual(result3_2['oriented_TP'], 3)
        self.assertEqual(result3_2['oriented_FN'], 2)
        self.assertEqual(result3_2['oriented_FP'], 0)

    def test_skeletal_confusion_matrix_results(self):
        tg1 = picause.arrowstr2pairlist("A --> B, C --> B, C --> D")
        dg1 = picause.arrowstr2pairlist("A --> B, C --> B, C --- D")
        result1 = picause.confusion_matrix(4, tg1, dg1)
        self.assertEqual(result1, (3, 0, 0, 3))

        tg2 = picause.arrowstr2pairlist("A --> B, A --> C")
        dg2 = picause.arrowstr2pairlist("B --> A, A --- C")
        result2 = picause.confusion_matrix(3, tg2, dg2)
        self.assertEqual(result2, (2, 0, 0, 1))

        tg3 = picause.arrowstr2pairlist("A --> B, B --> C, D --> B, B --> E, D --> F, E --> F")
        dg3 = picause.arrowstr2pairlist("A --> B, D --> B, B --> E, D --- E, D --- F, E --- F")
        result3 = picause.confusion_matrix(6, tg3, dg3)
        self.assertEqual(result3, (5, 1, 1, 8))

    def test_adjacencystr2arrowstr(self):
        s = picause.adjacencystr2arrowstr(self.graphstr)
        self.assertTrue(s[-1].isdigit())

    def test_SEM(self):
        pl = picause.adjacencystr2pairlist(self.graphstr)
        sem = picause.StructuralEquationDagModel(num_var=10,
                                                 E=pl,
                                                 seed=self.seed)
        self.assertEqual(len(sem.model['x_1']), 0)
        self.assertEqual(len(sem.model['x_10']), 2)
        data = sem.generate_data(102400)
        self.assertTrue(data.at[13352, 'x_1'] - 1.8489197455815802 < 0.001)


class TestDiscover(unittest.TestCase):
    def setUp(self):
        seed1 = 977351692186939434046756
        graphstr1 = "050409;06020508;010704;090A;070A;0308;"
        self.args1 = discover.argsClass(10, 0.1, 1, graphstr1, seed1, 1,
                                        verbose=False, algorithm="pc")

    def test_discovery(self):
        results = discover.discover(self.args1)
        self.assertEqual(len(results), 4)


if __name__ == "__main__":
    unittest.main()
