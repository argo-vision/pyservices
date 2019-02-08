import unittest
from pyservices import delete
import pyservices as ps


class TestDecoratorAddedInfo(unittest.TestCase):
    def test_delete(self):
        # A decorated "method":
        @ps.delete()
        def a_delete_op(): pass

        # Check of the content:
        iface = a_delete_op.rest_interface
        self.assertIsNotNone(iface)
        self.assertIsNotNone(iface.get('method'))
        self.assertEqual('DELETE', iface.get('method'))


if __name__ == '__main__':
    unittest.main()

