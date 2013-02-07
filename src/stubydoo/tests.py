import inspect
import stubydoo
import unittest


class TestStubMethod(unittest.TestCase):

    def repeat_with_method_defined(method_name, returning=None):
        if returning is None:
            returning = object()

        def repeat_with_method_defined(test):
            def method(self):
                returning
            method.__name__ = method_name

            double_type = type('double', (object,), {})
            double_type_with_method = type('double', (object,), {
                method_name: method
            })

            def original_test(self):
                self.double = double_type()
                return test(self)
            original_test.__name__ = test.__name__

            def test_with_method_defined(self):
                self.double = double_type_with_method()
                return test(self)
            test_with_method_defined.__name__ = (test.__name__ +
                                                 '_with_method_defined')

            f_locals = inspect.currentframe(1).f_locals
            f_locals[test_with_method_defined.__name__] = \
                test_with_method_defined

            return original_test
        return repeat_with_method_defined

    def _stub(self, object, method_name):
        if hasattr(object, method_name):
            return stubydoo.stub(getattr(object, method_name))
        return stubydoo.stub(object, method_name)

    @repeat_with_method_defined('method')
    def test_stubbing(self):
        self._stub(self.double, 'method')
        self.assertTrue(self.double.method() is None)

    @repeat_with_method_defined('method')
    def test_stub_with_return_value(self):
        value = object()
        self._stub(self.double, 'method').and_return(value)
        self.assertTrue(self.double.method() is value)

    @repeat_with_method_defined('method')
    def test_calling_stub_with_return_value_with_any_args(self):
        value = object()
        self._stub(self.double, 'method').and_return(value)
        self.assertTrue(self.double.method('any args') is value)

    @repeat_with_method_defined('method')
    def test_stub_with_args(self):
        self._stub(self.double, 'method').with_args('arg', 1, foo='bar')
        self.assertTrue(self.double.method('arg', 1, foo='bar') is None)

    @repeat_with_method_defined('method')
    def test_stub_with_args_with_return_value(self):
        value = object()
        self._stub(self.double, 'method').with_args('arg', 1, foo='bar').\
            and_return(value)
        self.assertTrue(self.double.method('arg', 1, foo='bar') is value)

    @repeat_with_method_defined('method')
    def test_calling_stub_with_wrong_args(self):
        self._stub(self.double, 'method').with_args('arg', 1, foo='bar')
        self.assertRaises(stubydoo.UnexpectedCallError,
                          self.double.method,
                          'wrong argument')

    @repeat_with_method_defined('method')
    def test_calling_stub_with_fallback_for_wrong_args(self):
        value = object()
        other_value = object()
        self._stub(self.double, 'method').and_return(value)
        self._stub(self.double, 'method').with_args('arg', 1, foo='bar').\
            and_return(other_value)
        self.assertTrue(self.double.method('any args') is value)

    @repeat_with_method_defined('__call__', 'original value')
    def test_stubbing_special_method(self):
        value = object()
        self._stub(self.double, '__call__').and_return(value)
        self.assertTrue(self.double() is value)


class TestStubCallsInExistingMethod(unittest.TestCase):

    def setUp(self):
        original_value = self.original_value = object()
        method = lambda self: original_value
        method.__name__ = 'method'
        obj_type = type('object', (object,), dict(method=method))
        self.object = obj_type()

    def test_stubbing(self):
        new_value = object()
        stubydoo.stub(self.object.method).and_return(new_value)
        self.assertTrue(self.object.method() is new_value)


class TestUnstubbingUnstubbedMethod(unittest.TestCase):

    def setUp(self):
        method = lambda self: 'some return value'
        method.__name__ = 'method'
        obj_type = type('object', (object,), dict(method=method))
        self.object = obj_type()

    def test_fails_silently(self):
        stubydoo.unstub(self.object.method)


class TestUnstubbingCallsInNonExistingMethod(unittest.TestCase):

    def setUp(self):
        self.double = stubydoo.double()

    def test_unstubbing(self):
        stubydoo.stub(self.double, 'method')
        stubydoo.unstub(self.double.method)

        try:
            self.double.method
        except AttributeError:
            pass
        else:
            self.fail()


class TestUnstubbingCallsInExistingMethod(unittest.TestCase):

    def setUp(self):
        original_value = self.original_value = object()
        method = lambda self: original_value
        method.__name__ = 'method'
        obj_type = type('object', (object,), dict(method=method))
        self.object = obj_type()

    def test_unstub_returns_back_original_method(self):
        stubydoo.stub(self.object.method)
        stubydoo.unstub(self.object.method)
        self.assertTrue(self.object.method() is self.original_value)

    def test_unstub_returns_back_original_method_even_in_multiple_stubs(self):
        other_value = object()
        stubydoo.stub(self.object.method)
        stubydoo.stub(self.object.method).with_args('arg', 1, foo='bar').\
            and_return(other_value)
        stubydoo.unstub(self.object.method)
        self.assertTrue(self.object.method() is self.original_value)

    def test_unset_in_fallback_keeps_more_specific_stub(self):
        value = object()
        other_value = object()
        generic = stubydoo.stub(self.object.method).and_return(other_value)
        stubydoo.stub(self.object.method).with_args('arg', 1, foo='bar').\
            and_return(value)

        generic.unset()
        self.assertTrue(self.object.method('arg', 1, foo='bar') is value)

    def test_unset_in_specific_keeps_generic_stub(self):
        value = object()
        other_value = object()
        stubydoo.stub(self.object.method).and_return(value)
        specific = stubydoo.stub(self.object.method).\
            with_args('arg', 1, foo='bar').and_return(other_value)

        specific.unset()
        self.assertTrue(self.object.method('any args') is value)


class TestStubAttributes(unittest.TestCase):

    def setUp(self):
        self.double = stubydoo.double()

    def test_stub_existing_attribute(self):
        self.double.foo = 'bar'
        stubydoo.stub(self.double, foo='baz')
        self.assertEquals(self.double.foo, 'baz')

    def test_stub_non_existing_attribute(self):
        stubydoo.stub(self.double, foo='baz')
        self.assertEquals(self.double.foo, 'baz')

    def test_unstub_existing_attribute(self):
        self.double.foo = 'bar'
        stubydoo.stub(self.double, foo='baz')
        stubydoo.unstub(self.double, 'foo')
        self.assertEquals(self.double.foo, 'bar')

    def test_unstub_non_existing_attribute(self):
        stubydoo.stub(self.double, foo='baz')
        stubydoo.unstub(self.double, 'foo')
        self.assertTrue(not hasattr(self.double, 'foo'))


# TODO
# class TestStubDataDescriptors(unittest.TestCase):
# 
#     def setUp(self):
#         class FooProp(object):
#             def __get__(self, instance, type=None):
#                 return '**' + instance._foo + '**'
#             def __set__(self, instance, value):
#                 instance._foo = value
# 
#         class mydouble(object):
#             foo = FooProp()
# 
#         self.double = mydouble()
# 
#     def test_stub(self):
#         self.double.foo = 'bar'
#         stubydoo.stub(self.double, foo='baz')
#         self.assertEquals(self.double.foo, 'baz')
# 
#     def test_unstub(self):
#         self.double.foo = 'bar'
#         stubydoo.stub(self.double, foo='baz')
#         stubydoo.unstub(self.double, 'foo')
#         self.assertEquals(self.double.foo, 'bar')
# 
# 
# class TestStubReadonlyProperty(unittest.TestCase):
# 
#     def setUp(self):
#         class mydouble(object):
#             @property
#             def foo(self):
#                 return self._foo
# 
#         self.double = mydouble()
# 
#     def test_stub(self):
#         self.double._foo = 'bar'
#         stubydoo.stub(self.double, foo='baz')
#         self.assertEquals(self.double.foo, 'baz')
# 
#     def test_unstub(self):
#         self.double._foo = 'bar'
#         stubydoo.stub(self.double, foo='baz')
#         stubydoo.unstub(self.double, 'foo')
#         self.assertEquals(self.double.foo, 'bar')


class TestArgumentMatching(unittest.TestCase):
    """Argument matching.

    Well-behaviored matchers should provide an __eq__ method.  The
    __eq__ method must keep a good semantic with other matchers of the
    same class.  For other items being matched relevant logic should be
    applied.
    """

    def setUp(self):
        class DictIncludingMatcher(object):
            """A matcher for dicts including required keys and values.
            """
            def __init__(self, kw):
                self.expected_keys_and_values = kw

            def __eq__(self, actual_dict):
                if isinstance(actual_dict, type(self)):
                    return (self.expected_keys_and_values ==
                            actual_dict.expected_keys_and_values)
                elif not isinstance(actual_dict, dict):
                    return False
                invalid = object()
                for key, expected in self.expected_keys_and_values.items():
                    actual = actual_dict.get(key, invalid)
                    if actual is invalid or not expected == actual:
                        return False
                return True

        self.double = stubydoo.double()
        self.dict_including = lambda **kw: DictIncludingMatcher(kw)

    def test_argument_matching(self):
        stubydoo.stub(self.double, 'method').and_return('not matched')
        stubydoo.stub(self.double, 'method').\
            with_args(self.dict_including(foo='bar', spam='eggs')).\
            and_return('matched')

        returned_value = self.double.method(dict(
            foo='bar', spam='eggs', some_other_key='some other value'
        ))
        self.assertEquals(returned_value, 'matched')

    def test_keyword_argument_matching(self):
        stubydoo.stub(self.double, 'method').and_return('not matched')
        stubydoo.stub(self.double, 'method').\
            with_kwargs(self.dict_including(foo='bar', spam='eggs')).\
            and_return('matched')

        returned_value = self.double.method(
            foo='bar', spam='eggs', some_other_key='some other value'
        )
        self.assertEquals(returned_value, 'matched')

    def test_positional_and_keyword_argument_matching(self):
        stubydoo.stub(self.double, 'method').and_return('not matched')
        stubydoo.stub(self.double, 'method').\
            with_args(self.dict_including(foo='bar')).\
            with_kwargs(self.dict_including(foo='bar', spam='eggs')).\
            and_return('matched')

        returned_value = self.double.method(
            dict(foo='bar', some_other_key='some other value'),
            foo='bar', spam='eggs', some_other_key='some other value'
        )
        self.assertEquals(returned_value, 'matched')

    def test_multiple_positional_and_keyword_argument_matching(self):
        stubydoo.stub(self.double, 'method').and_return('not matched')
        stubydoo.stub(self.double, 'method').\
            with_args(self.dict_including(foo='bar')).\
            with_kwargs(self.dict_including(foo='bar', spam='eggs')).\
            and_return('matched')
        stubydoo.stub(self.double, 'method').\
            with_args(self.dict_including(foo='bar')).\
            with_kwargs(self.dict_including(key='value')).\
            and_return('not matched')
        stubydoo.stub(self.double, 'method').\
            with_args(self.dict_including(key='value')).\
            with_kwargs(self.dict_including(foo='bar', spam='eggs')).\
            and_return('not matched')

        returned_value = self.double.method(
            dict(foo='bar', some_other_key='some other value'),
            foo='bar', spam='eggs', some_other_key='some other value'
        )
        self.assertEquals(returned_value, 'matched')

    def test_fallback_when_there_is_no_match(self):
        stubydoo.stub(self.double, 'method').and_return('not matched')
        stubydoo.stub(self.double, 'method').\
            with_args(self.dict_including(foo='bar')).\
            with_kwargs(self.dict_including(foo='bar', spam='eggs')).\
            and_return('matched')

        returned_value = self.double.method(
            dict(foo='bar', some_other_key='some other value'),
            some_other_key='some other value'
        )
        self.assertEquals(returned_value, 'not matched')


class TestStubException(unittest.TestCase):

    def setUp(self):
        class MyError(Exception):
            pass
        self.double = stubydoo.double()
        self.error = MyError

    def test_without_arguments(self):
        stubydoo.stub(self.double, 'method').and_raise(self.error)
        self.assertRaises(self.error, self.double.method)

    def test_with_arguments(self):
        stubydoo.stub(self.double, 'method').and_raise(StandardError)
        stubydoo.stub(self.double, 'method').with_args(1).and_raise(self.error)
        self.assertRaises(self.error, self.double.method, 1)

    def test_with_exception_arguments(self):
        class MyError(Exception):
            def __init__(self, *args, **kwargs):
                self.args = args
                self.kwargs = kwargs
        self.error = MyError
        stubydoo.stub(self.double, 'method').\
            and_raise(self.error, 'a1', 'a2', a3='a3', a4='a4')
        try:
            self.double.method()
        except MyError as exc:
            self.assertEquals(exc.args, ('a1', 'a2'))
            self.assertEquals(exc.kwargs, {'a3': 'a3', 'a4': 'a4'})
        else:
            self.fail('Expected to have an error raised')


class TestStubUsingCustomFunctionAsReturningValue(unittest.TestCase):

    def setUp(self):
        self.double = stubydoo.double()

    def test_stubbing_using_function(self):
        def fn():
            return 'returned from function'
        stubydoo.stub(self.double, 'method').and_run(fn)
        self.assertEquals(self.double.method(), 'returned from function')

    def test_function_arguments(self):
        def fn(*args, **kw):
            return (args, kw)

        stubydoo.stub(self.double, 'method').\
            with_args('a', 'b', a='a', b='b').and_run(fn)

        self.assertEquals(self.double.method('a', 'b', a='a', b='b'),
                          (('a', 'b'), {'a': 'a', 'b': 'b'}))


class TestStubIterator(unittest.TestCase):

    def setUp(self):
        self.double = stubydoo.double()

    def test_stubbing_iterator(self):
        value1 = object()
        value2 = object()

        @stubydoo.assert_expectations
        def test():
            stubydoo.stub(self.double, 'method').and_yield(value1, value2)
            return [v for v in self.double.method()]

        self.assertTrue(test() == [value1, value2])

    def test_stubbing_iterator_using_real_iterator(self):
        value1 = object()
        value2 = object()

        def iterator(*args, **kw):
            yield value1
            yield value2

        def test():
            stubydoo.stub(self.double, 'method').and_yield(iterator)
            return [v for v in self.double.method()]

        self.assertTrue(test() == [value1, value2])

    def test_iterator_arguments(self):
        def iterator(*args, **kw):
            for arg in args:
                yield arg
            for key in sorted(kw.keys()):
                yield key
            for value in sorted(kw.values()):
                yield value

        def test():
            stubydoo.stub(self.double, 'method').\
                with_args('a', 'b', a='a', b='b').and_yield(iterator)
            return [v for v in self.double.method('a', 'b', a='a', b='b')]

        self.assertTrue(test() == ['a', 'b', 'a', 'b', 'a', 'b'])


class TestExpectations(unittest.TestCase):

    def setUp(self):
        self.double = stubydoo.double()

    def test_no_expectation_generates_no_error(self):
        @stubydoo.assert_expectations
        def test():
            pass
        test()

    def test_expectation_in_method_stub_generates_no_error(self):
        @stubydoo.assert_expectations
        def test():
            stubydoo.stub(self.double, 'method').and_return('a value')

        test()

    def test_expectation_met(self):
        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(self.double, 'method')
            self.double.method()
        try:
            test()
        except stubydoo.ExpectationNotSatisfiedError:
            self.fail()

    def test_expectation_after_method_stub_met(self):
        @stubydoo.assert_expectations
        def test():
            stubydoo.stub(self.double, 'method')
            stubydoo.expect(self.double, 'method')
            self.double.method()
        try:
            test()
        except stubydoo.ExpectationNotSatisfiedError:
            self.fail()

    def test_expectation_not_met(self):
        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(self.double, 'method')
        try:
            test()
        except AssertionError:
            pass
        else:
            self.fail()

    def test_expectation_met_in_object_with_existing_method(self):
        class myobject(object):
            def method(self):
                None
        obj = myobject()

        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(obj, 'method')
            obj.method()
        try:
            test()
        except stubydoo.ExpectationNotSatisfiedError:
            self.fail()

    def test_expectation_met_in_object_referencing_existing_method(self):
        class myobject(object):
            def method(self):
                None
        obj = myobject()

        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(obj.method)
            obj.method()
        try:
            test()
        except stubydoo.ExpectationNotSatisfiedError:
            self.fail()

    def test_expectation_not_met_in_object_with_existing_method(self):
        class myobject(object):
            def method(self):
                None
        obj = myobject()

        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(obj, 'method')
        try:
            test()
        except AssertionError:
            pass
        else:
            self.fail()

    def test_expectation_not_met_in_object_referencing_existing_method(self):
        class myobject(object):
            def method(self):
                None
        obj = myobject()

        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(obj.method)
        try:
            test()
        except AssertionError:
            pass
        else:
            self.fail()

    def test_expectation_with_return_value(self):
        value = object()

        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(self.double, 'method').and_return(value)
            return self.double.method()

        self.assertTrue(test() is value)

    def test_expectation_with_exact_number_of_calls_met(self):
        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(self.double, 'method').exactly(2).times
            self.double.method()
            self.double.method()

        test()

    def test_expectation_with_exact_number_of_calls_exceeded(self):
        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(self.double, 'method').exactly(2).times
            self.double.method()
            self.double.method()
            self.double.method()

        self.assertRaises(stubydoo.ExpectationNotSatisfiedError, test)

    def test_expectation_with_exact_number_of_calls_not_reached(self):
        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(self.double, 'method').exactly(2).times
            self.double.method()

        self.assertRaises(stubydoo.ExpectationNotSatisfiedError, test)

    def test_expectation_with_minimun_number_of_calls_not_reached(self):
        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(self.double, 'method').at_least(2).times
            self.double.method()

        self.assertRaises(stubydoo.ExpectationNotSatisfiedError, test)

    def test_expectation_with_minimun_number_of_calls_reached_is_met(self):
        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(self.double, 'method').at_least(2).times
            self.double.method()
            self.double.method()

        test()

    def test_expectation_with_minimun_number_of_calls_exceeded_is_met(self):
        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(self.double, 'method').at_least(2).times
            self.double.method()
            self.double.method()
            self.double.method()

        test()

    def test_expectation_with_maximum_number_of_calls_exceeded(self):
        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(self.double, 'method').at_most(2).times
            self.double.method()
            self.double.method()
            self.double.method()

        self.assertRaises(stubydoo.ExpectationNotSatisfiedError, test)

    def test_expectation_with_maximum_number_of_calls_is_reached(self):
        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(self.double, 'method').at_most(2).times
            self.double.method()
            self.double.method()

        test()

    def test_expectation_with_maximum_number_of_calls_is_not_reached(self):
        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(self.double, 'method').at_most(2).times
            self.double.method()

        test()

    def test_expectation_with_range_of_calls_not_reached(self):
        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(self.double, 'method').at_most(4).times.\
                at_least(2).times
            self.double.method()

        self.assertRaises(stubydoo.ExpectationNotSatisfiedError, test)

    def test_expectation_with_range_of_calls_in_minimum(self):
        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(self.double, 'method').at_most(4).times.\
                at_least(2).times
            self.double.method()
            self.double.method()

        test()

    def test_expectation_with_range_of_calls_fullfilled(self):
        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(self.double, 'method').at_most(4).times.\
                at_least(2).times
            self.double.method()
            self.double.method()
            self.double.method()

        test()

    def test_expectation_with_range_of_calls_in_maximum(self):
        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(self.double, 'method').at_most(4).times.\
                at_least(2).times
            self.double.method()
            self.double.method()
            self.double.method()
            self.double.method()

        test()

    def test_expectation_with_range_of_calls_exceeded(self):
        @stubydoo.assert_expectations
        def test():
            stubydoo.expect(self.double, 'method').at_most(4).times.\
                at_least(2).times
            self.double.method()
            self.double.method()
            self.double.method()
            self.double.method()
            self.double.method()

        self.assertRaises(stubydoo.ExpectationNotSatisfiedError, test)

    def test_once_works_as_exactly_one(self):
        @stubydoo.assert_expectations
        def not_reached():
            stubydoo.expect(self.double, 'method').once
        self.assertRaises(stubydoo.ExpectationNotSatisfiedError, not_reached)

        @stubydoo.assert_expectations
        def reached():
            stubydoo.expect(self.double, 'method').once
            self.double.method()
        reached()  # ok

        @stubydoo.assert_expectations
        def exceeded():
            stubydoo.expect(self.double, 'method').once
            self.double.method()
            self.double.method()
        self.assertRaises(stubydoo.ExpectationNotSatisfiedError, exceeded)

    def test_twice_works_as_exactly_two(self):
        @stubydoo.assert_expectations
        def not_reached():
            stubydoo.expect(self.double, 'method').twice
            self.double.method()
        self.assertRaises(stubydoo.ExpectationNotSatisfiedError, not_reached)

        @stubydoo.assert_expectations
        def reached():
            stubydoo.expect(self.double, 'method').twice
            self.double.method()
            self.double.method()
        reached()  # ok

        @stubydoo.assert_expectations
        def exceeded():
            stubydoo.expect(self.double, 'method').twice
            self.double.method()
            self.double.method()
            self.double.method()
        self.assertRaises(stubydoo.ExpectationNotSatisfiedError, exceeded)

    def test_expectation_with_exactly_zero_calls_reached(self):
        @stubydoo.assert_expectations
        def reached():
            stubydoo.expect(self.double, 'method').exactly(0).times
        reached()

    def test_expectation_with_exactly_zero_calls_exceeded(self):
        @stubydoo.assert_expectations
        def exceeded():
            stubydoo.expect(self.double, 'method').exactly(0).times
            self.double.method()
        self.assertRaises(stubydoo.ExpectationNotSatisfiedError, exceeded)

    def test_expectation_with_at_most_zero_calls_reached(self):
        @stubydoo.assert_expectations
        def reached():
            stubydoo.expect(self.double, 'method').at_most(0).times
        reached()  #ok

    def test_expectation_with_at_most_zero_calls_exceeded(self):
        @stubydoo.assert_expectations
        def exceeded():
            stubydoo.expect(self.double, 'method').at_most(0).times
            self.double.method()
        self.assertRaises(stubydoo.ExpectationNotSatisfiedError, exceeded)

    def test_expectation_that_must_not_be_called_should_work_as_exactly_zero_calls(self):
        @stubydoo.assert_expectations
        def reached():
            stubydoo.expect(self.double, 'method').to_not_be_called
        reached()  #ok

        @stubydoo.assert_expectations
        def exceeded():
            stubydoo.expect(self.double, 'method').to_not_be_called
            self.double.method()

        self.assertRaises(stubydoo.ExpectationNotSatisfiedError, exceeded)


class TestFunctionStub(unittest.TestCase):
    # Function stubs are currently handled by the `patch` function.  In the
    # future, this will be handled by `stub`.  Also, `expect` will handle
    # function patches in a way that expectations about the call can be
    # asserted at some level.

    def setUp(self):
        self.double = stubydoo.double()

    def test_function_code_is_replaced(self):
        a, b = 1, 2

        def original_function(c, d=-6):
            return a + b + c + d

        @stubydoo.assert_expectations
        def test():
            @stubydoo.patch(original_function)
            def patched_function(c, d=4):
                return c + d

            self.assertEquals(original_function(3), 7)

        test()

    def test_function_code_is_restored_after_test_is_run(self):
        def original_function():
            return 1

        @stubydoo.assert_expectations
        def test():
            @stubydoo.patch(original_function)
            def patched_function():
                return 2

        test()
        self.assertEquals(original_function(), 1)


class TestExpectationAssertionNotAsADecorator(unittest.TestCase):

    def setUp(self):
        self.double = stubydoo.double()

    def test_failing_assertion(self):
        stubydoo.expect(self.double, 'method')

        self.assertRaises(stubydoo.ExpectationNotSatisfiedError,
                          stubydoo.assert_expectations)

    def test_successful_assertion(self):
        stubydoo.expect(self.double, 'method')
        self.double.method()

        stubydoo.assert_expectations()


class TestExpectationErrorWhenNotVerifiedPreviousOnes(unittest.TestCase):

    def setUp(self):
        self.double = stubydoo.double()

    def test_assertions_not_verified(self):

        def test():
            stubydoo.expect(self.double, 'method')

        @stubydoo.assert_expectations
        def other_test():
            stubydoo.expect(self.double, 'other_method')

        test()
        self.assertRaises(stubydoo.ExpectationsNotVerifiedError, other_test)

    def tearDown(self):
        try:
            stubydoo.assert_expectations()
        except stubydoo.ExpectationNotSatisfiedError:
            pass


class TestAssertionDecoratorInClasses(unittest.TestCase):

    def test_failing_assertion(self):
        @stubydoo.assert_expectations
        class TestCase(object):
            def __init__(self):
                self.double = stubydoo.double()

            def test_something(self):
                stubydoo.expect(self.double, 'method')

        self.assertRaises(stubydoo.ExpectationNotSatisfiedError,
                          TestCase().test_something)

    def test_successful_assertion(self):
        @stubydoo.assert_expectations
        class TestCase(object):
            def __init__(self):
                self.double = stubydoo.double()

            def test_something(self):
                stubydoo.expect(self.double, 'method')
                self.double.method()
        try:
            TestCase().test_something()
        except stubydoo.ExpectationNotSatisfiedError:
            self.fail()


class TestDouble(unittest.TestCase):

    def test_attributes(self):
        double = stubydoo.double(attribute='value')
        self.assertEquals(double.attribute, 'value')

    def test_methods_using_lambda_can_be_stubbed(self):
        double = stubydoo.double(method=lambda self: 'value')
        stubydoo.stub(double.method).and_return('another value')
        self.assertEquals(double.method(), 'another value')


class TestMock(unittest.TestCase):

    def test_attributes(self):
        mock = stubydoo.mock(attribute='value')
        self.assertEquals(mock.attribute, 'value')

    def test_missing_attribute_access(self):
        def access_attribute():
            stubydoo.mock().attribute
        self.assertRaises(stubydoo.UnexpectedAttributeAccessError,
                          access_attribute)
        self.assertRaises(AssertionError, access_attribute)

    def test_methods_using_lambda_can_be_stubbed(self):
        mock = stubydoo.mock(method=lambda self: 'value')
        stubydoo.stub(mock.method).and_return('another value')
        self.assertEquals(mock.method(), 'another value')


class TestNull(unittest.TestCase):

    def setUp(self):
        self.null = stubydoo.null()

    def test_attributes(self):
        null = stubydoo.null(attribute='value')
        self.assertEquals(null.attribute, 'value')

    def test_methods_using_lambda_can_be_stubbed(self):
        null = stubydoo.null(method=lambda self: 'value')
        stubydoo.stub(null.method).and_return('another value')
        self.assertEquals(null.method(), 'another value')

    def test_null_can_be_positivated(self):
        self.assertTrue((+self.null) is self.null)

    def test_null_can_be_negated(self):
        self.assertTrue((-self.null) is self.null)

    def test_null_absolute_value(self):
        self.assertTrue(abs(self.null) is self.null)

    def test_null_addition_with_null(self):
        self.assertTrue((self.null + self.null) is self.null)

    def test_null_addition_with_other(self):
        self.assertTrue((self.null + 1) is self.null)

    def test_null_addition_with_other_reflected(self):
        self.assertTrue((1 + self.null) is self.null)

    def test_null_subtraction_with_null(self):
        self.assertTrue((self.null - self.null) is self.null)

    def test_null_subtraction_with_other(self):
        self.assertTrue((self.null - 1) is self.null)

    def test_null_subtraction_with_other_reflected(self):
        self.assertTrue((1 - self.null) is self.null)

    def test_null_multiplication_with_null(self):
        self.assertTrue((self.null * self.null) is self.null)

    def test_null_multiplication_with_other(self):
        self.assertTrue((self.null * 1) is self.null)

    def test_null_multiplication_with_other_reflected(self):
        self.assertTrue((1 * self.null) is self.null)

    def test_null_division_with_null(self):
        self.assertTrue((self.null / self.null) is self.null)

    def test_null_division_with_other(self):
        self.assertTrue((self.null / 1) is self.null)

    def test_null_division_with_other_reflected(self):
        self.assertTrue((1 / self.null) is self.null)

    def test_null_integer_division_with_null(self):
        self.assertTrue((self.null // self.null) is self.null)

    def test_null_integer_division_with_other(self):
        self.assertTrue((self.null // 1) is self.null)

    def test_null_integer_division_with_other_reflected(self):
        self.assertTrue((1 // self.null) is self.null)

    def test_null_modulo_null(self):
        self.assertTrue((self.null % self.null) is self.null)

    def test_null_modulo_other(self):
        self.assertTrue((self.null % 1) is self.null)

    def test_null_modulo_other_reflected(self):
        self.assertTrue((1 % self.null) is self.null)

    def test_null_exponentiation_with_null(self):
        self.assertTrue((self.null ** self.null) is self.null)

    def test_null_exponentiation_with_other(self):
        self.assertTrue((self.null ** 1) is self.null)

    def test_null_exponentiation_with_other_reflected(self):
        self.assertTrue((1 ** self.null) is self.null)

    def test_null_left_bitwise_shift_with_null(self):
        self.assertTrue((self.null << self.null) is self.null)

    def test_null_left_bitwise_shift_with_other(self):
        self.assertTrue((self.null << 1) is self.null)

    def test_null_left_bitwise_shift_with_other_reflected(self):
        self.assertTrue((1 << self.null) is self.null)

    def test_null_right_bitwise_shift_with_null(self):
        self.assertTrue((self.null >> self.null) is self.null)

    def test_null_right_bitwise_shift_with_other(self):
        self.assertTrue((self.null >> 1) is self.null)

    def test_null_right_bitwise_shift_with_other_reflected(self):
        self.assertTrue((1 >> self.null) is self.null)

    def test_null_bitwise_and_with_null(self):
        self.assertTrue((self.null & self.null) is self.null)

    def test_null_bitwise_and_with_other(self):
        self.assertTrue((self.null & 1) is self.null)

    def test_null_bitwise_and_with_other_reflected(self):
        self.assertTrue((1 & self.null) is self.null)

    def test_null_bitwise_or_with_null(self):
        self.assertTrue((self.null | self.null) is self.null)

    def test_null_bitwise_or_with_other(self):
        self.assertTrue((self.null | 1) is self.null)

    def test_null_bitwise_or_with_other_reflected(self):
        self.assertTrue((1 | self.null) is self.null)

    def test_null_bitwise_xor_with_null(self):
        self.assertTrue((self.null ^ self.null) is self.null)

    def test_null_bitwise_xor_with_other(self):
        self.assertTrue((self.null ^ 1) is self.null)

    def test_null_bitwise_xor_with_other_reflected(self):
        self.assertTrue((1 ^ self.null) is self.null)

    def test_null_attribute_reading(self):
        self.assertTrue(self.null.foo is self.null)

    def test_null_attribute_writing(self):
        self.null.foo = 1
        self.assertTrue(self.null.foo == 1)

    def test_null_attribute_deleting(self):
        del self.null.foo
        self.assertTrue(self.null.foo is self.null)

    def test_null_item_reading(self):
        self.assertTrue(self.null['foo'] is self.null)

    def test_null_item_writing(self):
        self.null['foo'] = 1
        self.assertTrue(self.null['foo'] is self.null)

    def test_null_item_deleting(self):
        del self.null['foo']
        self.assertTrue(self.null['foo'] is self.null)

    def test_calling_null(self):
        self.assertTrue(self.null() is self.null)

    def test_calling_null_with_arbitrary_arguments(self):
        self.assertTrue(self.null('arg', 1, foo='bar') is self.null)
