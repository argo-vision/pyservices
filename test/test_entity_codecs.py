import unittest
import pyservices as ps


class TestUtils(unittest.TestCase):

    def setUp(self):
        self.inst_c = C('val_memb_c_1', 'val_memb_c_2')
        self.inst_b = B('val_memb_b', self.inst_c)
        self.inst_a = A('val_memb_a', self.inst_b)
        self.dict_inst = {
            'memb_a': 'val_memb_a',
            'inst_b': {
                'memb_b': 'val_memb_b',
                'inst_c': {
                    'memb_c_1': 'val_memb_c_1',
                    'memb_c_2': 'val_memb_c_2'
                }
            }
        }

    def test_get(self):
        self.assertEqual(ps.entity_codecs.get(self.inst_a, 'memb_a'), 'val_memb_a')

    def test_instance_attributes(self):
        self.assertListEqual(ps.entity_codecs.instance_attributes(self.inst_c),['memb_c_1', 'memb_c_2'])

    def test_dict_to_instance(self):
        inst = ps.entity_codecs.dict_to_instance(self.dict_inst, A)
        self.assertEqual(inst.memb_a, 'val_memb_a')
        self.assertTrue(isinstance(inst.inst_b, B))
        self.assertEqual(inst.inst_b.memb_b, 'val_memb_b')
        self.assertTrue(isinstance(inst.inst_b.inst_c, C))
        self.assertEqual(inst.inst_b.inst_c.memb_c_1, 'val_memb_c_1')
        self.assertEqual(inst.inst_b.inst_c.memb_c_2, 'val_memb_c_2')

    # TODO: this approach is not flexible enough
    def test_instance_to_dict(self):
        pass


class TestJSON(unittest.TestCase):
    pass


class C:

    def __init__(self, memb_c_1, memb_c_2):
        self.memb_c_1 = memb_c_1
        self.memb_c_2 = memb_c_2

    def meth_c(self):
        pass


class B:
    subtypes = {
        'inst_c': C
    }

    def __init__(self, memb_b, inst_c):
        self.memb_b = memb_b
        self.inst_c = inst_c


class A:
    subtypes = {
        'inst_b': B
    }

    def __init__(self, memb_a, inst_b):
        self.memb_a = memb_a
        self.inst_b = inst_b


if __name__ == '__main__':
    unittest.main()
