import unittest
import pyservices as ps
from pyservices.data_descriptors import MetaModel


# TODO remove
class TestDecorator(unittest.TestCase):

    def setUp(self):
        MetaModel.modelClasses = dict()
        self.metaModel = MetaModel('Model')
        self.an_op = lambda: None

    def test_delete(self):
        # A decorated "method":
        ps.rest_delete(self.metaModel)(self.an_op)
        self._testIfaceItems(operation='delete')

    def test_post(self):
        ps.rest_update(self.metaModel)(self.an_op)
        self._testIfaceItems(operation='update', consumes=ps.JSON)

    def test_put(self):
        ps.rest_add(self.metaModel)(self.an_op)
        self._testIfaceItems(operation='add', consumes=ps.JSON)

    def test_get(self):
        ps.rest_detail(self.metaModel)(self.an_op)
        self._testIfaceItems(operation='detail', produces=ps.JSON)

    def test_get_list(self):
        ps.rest_collection(self.metaModel)(self.an_op)
        self._testIfaceItems(operation='list', produces=ps.JSON)

    def _testIfaceExistence(self):
        iface = self.an_op.rest_interface
        self.assertIsNotNone(iface)

    def _testIfaceItems(self, **kwargs):
        self._testIfaceExistence()
        iface = self.an_op.rest_interface
        for k, v in kwargs.items():
            self.assertIsNotNone(iface.get(k))
            self.assertEqual(v, iface.get(k))


if __name__ == '__main__':
    unittest.main()

