import unittest
import pyservices as ps


class TestDecoratorAddedInfo(unittest.TestCase):

    def setUp(self):
        self.an_op = lambda: None

    def test_delete(self):
        # A decorated "method":
        ps.delete()(self.an_op)
        self._testIfaceItems(method='DELETE')

    def test_post(self):
        ps.post()(self.an_op)
        self._testIfaceItems(method='POST', consumes=ps.JSON)

    def test_put(self):
        ps.put()(self.an_op)
        self._testIfaceItems(method='PUT', consumes=ps.JSON)

    def test_get(self):
        ps.get()(self.an_op)
        self._testIfaceItems(method='GET', produces=ps.JSON)

    def test_get_list(self):
        ps.get_list()(self.an_op)
        self._testIfaceItems(method='GET', produces=ps.JSON)

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

