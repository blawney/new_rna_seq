import logging
logging.disable(logging.CRITICAL)

import unittest
import mock
import sys
import os

# for finding modules in the sibling directories
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from utils.util_classes import Params
from utils.custom_exceptions import *

class TestParams(unittest.TestCase):
	"""
	Tests the Params object.		
	"""

	def test_add_key_value_pair(self):
		p = Params()
		v = "some_value"
		p.add( key = v)
		self.assertEqual(p.get("key"), v)

	def test_add_multiple_key_value_pairs(self):
		p = Params()
		v1 = "some_value"
		v2 = "other_value"
		p.add( key1 = v1, key2 = v2)
		self.assertEqual(p.get("key1"), v1)
		self.assertEqual(p.get("key2"), v2)

	def test_add_dict(self):
		p = Params()
		d = {"a":1, "b":2}
		p.add(d)
		self.assertEqual(p.get("a"), 1)
		self.assertEqual(p.get("b"), 2)

	def test_add_multiple_dicts(self):
		p = Params()
		d1 = {"a":1, "b":2}
		d2 = {"c":3, "d":4}
		p.add(d1, d2)
		self.assertEqual(p.get("a"), 1)
		self.assertEqual(p.get("b"), 2)
		self.assertEqual(p.get("c"), 3)
		self.assertEqual(p.get("d"), 4)

	def test_add_both_simultaneously(self):
		p = Params()
		v = "some_value"
		d = {"a":1, "b":2}

		p.add(d, key = v)

		self.assertEqual(p.get("a"), 1)
		self.assertEqual(p.get("b"), 2)
		self.assertEqual(p.get("key"), v)

	def test_asking_for_missing_value_kills_pipeline(self):
		p = Params()

		# add some value. Not necessary to do this.
		v = "some_value"
		p.add( key = v)
		self.assertRaises(ParameterNotFoundException, p.get, "missing_val")

	def test_reset_param(self):
		p = Params()
		v = "some_value"
		p.add( key = v)
		p.reset_param('key', 'new_value')
		self.assertEqual(p.get('key'), 'new_value')


	def test_trying_to_reset_unset_param_raises_exception(self):
		with self.assertRaises(ParameterNotFoundException):
			p = Params()
			p.reset_param('key', 'new_value')


	def test_addition_of_param_objects(self):
		"""
		This tests the operator overload of '+'
		"""
		p1 = Params()
		p1.add( a = 1, b = 2)
		p2 = Params()
		p2.add( c = 3, d = 4)

		p3 = p1 + p2
		self.assertEqual(p3.get("a"), 1)
		self.assertEqual(p3.get("b"), 2)
		self.assertEqual(p3.get("c"), 3)
		self.assertEqual(p3.get("d"), 4)

	def test_shorthand_addition_of_param_objects(self):
		"""
		This tests the operator overload of '+'
		"""
		p1 = Params()
		p1.add( a = 1, b = 2)
		p2 = Params()
		p2.add( c = 3, d = 4)

		p1 += p2
		self.assertEqual(p1.get("a"), 1)
		self.assertEqual(p1.get("b"), 2)
		self.assertEqual(p1.get("c"), 3)
		self.assertEqual(p1.get("d"), 4)


	def test_prepend_executes_correctly(self):
		"""
		This tests that the method works as expected for various calls
		"""
		p1 = Params()
		p1.add(a='fileA.txt', b='fileB.txt')

		p1.prepend_param('a', '/path/to/prepend', os.path.join)
		self.assertEqual(p1.get('a'), os.path.join('/path/to/prepend/','fileA.txt'))

		p1.prepend_param('b', 'prefix', lambda x,y: x+':'+y)
		self.assertEqual(p1.get('b'), 'prefix:fileB.txt')


	def test_prepend_raises_exception_if_not_parameter_found(self):
		"""
		This tests that the method fails gracefully if the parameter was not located
		"""

		with self.assertRaises(ParameterNotFoundException):
			p = Params()
			p.prepend_param('a', '/path/to/prepend', os.path.join)
		

	def test_prepend_fails_if_callable_is_not_compatible(self):
		"""
		This tests that error is thrown if passed callable is not valid (E.g. if takes 3 args, etc)
		"""
		p1 = Params()
		p1.add(a='fileA.txt', b=1)

		def bad_method(x,y,z):
			return x+y+z

		# if method has wrong number of args
		with self.assertRaises(TypeError):
			p1.prepend_param('a', '/path/to/prepend', bad_method)

		# if try to add a integer and a string: (or other incompatible types)
		with self.assertRaises(TypeError):
			p1.prepend_param('b', 'prefix', lambda x,y: x+':'+y)


if __name__ == "__main__":
	unittest.main()
