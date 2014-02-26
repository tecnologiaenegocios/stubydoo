stubydoo
========

A mock/stub library for Python 2.x


Disclaimer
----------

This package is considered unstable.  API changes may happen without notice.
Not ready for public comsumption.


Usage example
-------------

This package provides a basic mocking/stubbing functionality for use in
test code.  It's possible to change the behavior of a method of any
non-builtin object:

  >>> from stubydoo import stub
  >>> class MyObject(object):
  ...     def get_foo(self):
  ...         return 'foo'
  >>> my_object = MyObject()
  >>> _ = stub(my_object.get_foo).and_return('bar')
  >>> my_object.get_foo()
  'bar'
