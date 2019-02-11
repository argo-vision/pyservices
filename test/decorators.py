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

    def test_post(self):
        @ps.post()
        def a_post_op(): pass

        iface = a_post_op.rest_interface
        self.assertIsNotNone(iface)

        method = iface.get('method')
        self.assertIsNotNone(method)
        self.assertEqual('POST', method)

        codec = iface.get('consumes')
        self.assertIsNotNone(codec)
        self.assertTrue(issubclass(codec, ps.Codec))
        self.assertEqual(ps.JSON, codec)

    def test_put(self):
        @ps.put()
        def a_put_op(): pass

        iface = a_put_op.rest_interface
        self.assertIsNotNone(iface)

        method = iface.get('method')
        self.assertIsNotNone(method)
        self.assertEqual('PUT', method)

        codec = iface.get('consumes')
        self.assertIsNotNone(codec)
        self.assertTrue(issubclass(codec, ps.Codec))
        self.assertEqual(ps.JSON, codec)

    def test_get(self):
        @ps.get()
        def a_get_op(): pass

        iface = a_get_op.rest_interface
        self.assertIsNotNone(iface)

        method = iface.get('method')
        self.assertIsNotNone(method)
        self.assertEqual('GET', method)

        codec = iface.get('produces')
        self.assertIsNotNone(codec)
        self.assertTrue(issubclass(codec, ps.Codec))
        self.assertEqual(ps.JSON, codec)

    def test_get_list(self):
        @ps.get()
        def a_get_list_op(): pass

        iface = a_get_list_op.rest_interface
        self.assertIsNotNone(iface)

        method = iface.get('method')
        self.assertIsNotNone(method)
        self.assertEqual('GET', method)

        codec = iface.get('produces')
        self.assertIsNotNone(codec)
        self.assertTrue(issubclass(codec, ps.Codec))
        self.assertEqual(ps.JSON, codec)


if __name__ == '__main__':
    unittest.main()

