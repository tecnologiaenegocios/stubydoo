import re

def double(**kw):
    return type('double', (object,), kw)()

def mock(**kw):
    def attribute_raiser(self, attribute):
        raise UnexpectedAttributeAccessError, attribute
    kw['__getattr__'] = attribute_raiser
    return type('mock', (object,), kw)()

def null(**kw):
    null_type = type('null', (object,), kw)
    null_type.__pos__       = lambda self:              self
    null_type.__neg__       = lambda self:              self
    null_type.__abs__       = lambda self:              self
    null_type.__add__       = lambda self, other:       self
    null_type.__radd__      = lambda self, other:       self
    null_type.__sub__       = lambda self, other:       self
    null_type.__rsub__      = lambda self, other:       self
    null_type.__mul__       = lambda self, other:       self
    null_type.__rmul__      = lambda self, other:       self
    null_type.__div__       = lambda self, other:       self
    null_type.__rdiv__      = lambda self, other:       self
    null_type.__floordiv__  = lambda self, other:       self
    null_type.__rfloordiv__ = lambda self, other:       self
    null_type.__mod__       = lambda self, other:       self
    null_type.__rmod__      = lambda self, other:       self
    null_type.__pow__       = lambda self, other:       self
    null_type.__rpow__      = lambda self, other:       self
    null_type.__lshift__    = lambda self, other:       self
    null_type.__rlshift__   = lambda self, other:       self
    null_type.__rshift__    = lambda self, other:       self
    null_type.__rrshift__   = lambda self, other:       self
    null_type.__and__       = lambda self, other:       self
    null_type.__rand__      = lambda self, other:       self
    null_type.__or__        = lambda self, other:       self
    null_type.__ror__       = lambda self, other:       self
    null_type.__xor__       = lambda self, other:       self
    null_type.__rxor__      = lambda self, other:       self
    null_type.__getattr__   = lambda self, attr:        self
    null_type.__setattr__   = lambda self, attr, value: self
    null_type.__delattr__   = lambda self, attr:        self
    null_type.__getitem__   = lambda self, key:         self
    null_type.__setitem__   = lambda self, key, value:  self
    null_type.__delitem__   = lambda self, key:         self
    null_type.__call__      = lambda self, *a, **kw:    self
    return null_type()

def _ensure_presence_of_expectations_object(instance):
    if not hasattr(instance, '_expectations_'):
        expectations = Expectations()
        expectations.patch_instance(instance)

_no_attribute_marker = object()

def stub(instance_or_method, method_name=None, **attributes):
    if attributes:
        instance = instance_or_method
        replaced_attributes = getattr(instance, '_replaced_attributes_', {})
        instance._replaced_attributes_ = replaced_attributes
        for attribute, value in attributes.items():
            original_value = getattr(instance, attribute, _no_attribute_marker)
            if attribute not in replaced_attributes:
                replaced_attributes[attribute] = original_value
            setattr(instance, attribute, value)
    else:
        if method_name is not None:
            instance = instance_or_method
        else:
            method = instance_or_method
            method_name = method.__name__
            instance = method.__self__
        _ensure_presence_of_expectations_object(instance)
        stub = MethodStub(instance, method_name)
        stub.set()
        return stub

def unstub(instance_or_method, *attributes):
    if attributes:
        instance = instance_or_method
        if not hasattr(instance, '_replaced_attributes_'):
            return
        replaced_attributes = instance._replaced_attributes_
        attributes = [a for a in attributes if a in replaced_attributes]
        for attribute in attributes:
            original_value = replaced_attributes[attribute]
            if original_value is _no_attribute_marker:
                delattr(instance, attribute)
            else:
                setattr(instance, attribute, original_value)
            del replaced_attributes[attribute]
    else:
        method = instance_or_method
        instance = method.__self__
        method_name = method.__name__
        expectations = getattr(instance, '_expectations_', None)
        if expectations:
            expectations[method_name].discard_all()
            del expectations[method_name]
            if not expectations:
                expectations.unpatch_instance()

def expect(instance_or_method, method_name=None):
    if method_name is not None:
        instance = instance_or_method
    else:
        method = instance_or_method
        method_name = method.__name__
        instance = method.__self__
    _ensure_presence_of_expectations_object(instance)
    expectation = MethodExpectation(instance, method_name)
    expectation.set()
    _instances_with_expectations.add(instance)
    return expectation

_test_method_re = re.compile(r'^test[a-zA-Z_]*$')
def assert_expectations(fn=None):
    def call_method_with_assertion(*args, **kw):
        try:
            if fn:
                if len(_instances_with_expectations) > 0:
                    raise ExpectationsNotVerifiedError
                value = fn(*args, **kw)
            else:
                value = None

            for expectations in _instances_with_expectations:
                if not expectations.is_satisfied():
                    raise ExpectationNotSatisfiedError
            return value
        finally:
            _clear_expectations()

    if fn:
        if isinstance(fn, type):
            cls = fn
            for attr in cls.__dict__.keys():
                if _test_method_re.match(attr):
                    setattr(cls, attr, assert_expectations(cls.__dict__[attr]))
            return cls
        else:
            return call_method_with_assertion
    else:
        call_method_with_assertion()

def _clear_expectations():
    for expectations in _instances_with_expectations:
        expectations.unpatch_instance()
    _instances_with_expectations.clear()


class ExpectationsNotVerifiedError(AssertionError):
    pass


class ExpectationNotSatisfiedError(AssertionError):
    pass


class UnexpectedAttributeAccessError(ExpectationNotSatisfiedError):
    pass


class UnexpectedCallError(UnexpectedAttributeAccessError):
    pass


class ExpectationArguments(object):

    def __init__(self, args, kwargs):
        self.args = args
        self.kwargs = kwargs

    def __eq__(self, other):
        if not isinstance(other, ExpectationArguments):
            return False
        return self.args == other.args and self.kwargs == other.kwargs

    def __str__(self):
        return "<Args positional: %r, keyword: %r>" % (self.args, self.kwargs)


class Expectations(dict):

    def __getitem__(self, method_name):
        if not method_name in self:
            self[method_name] = MethodExpectations(self.instance, method_name)
        return super(Expectations, self).__getitem__(method_name)

    def patch_instance(self, instance):
        self.instance = instance
        self.instance._old_class_ = self.instance.__class__
        new_class = type(self.instance.__class__.__name__,
                         (self.instance.__class__,),
                         {})
        self.instance.__class__ = new_class
        self.instance._expectations_ = self

    def unpatch_instance(self):
        self.expectations_with_arguments = []
        self.expectations_without_arguments = []
        self.instance.__class__ = self.instance._old_class_
        delattr(self.instance, '_old_class_')
        delattr(self.instance, '_expectations_')

    def is_satisfied(self):
        for method_expectation in self.values():
            if not method_expectation.is_satisfied():
                return False
        return True


class MethodExpectations(object):

    def __init__(self, instance, method_name):
        self.instance = instance
        self.method_name = method_name
        self.expectations_with_arguments = []
        self.expectations_without_arguments = []

    def add(self, expectation):
        if (not self.expectations_with_arguments and
            not self.expectations_without_arguments):
            self._add_method()

        if expectation.skip_arguments_verification:
            self.expectations_without_arguments.append(expectation)
        else:
            self._add_expectation_with_arguments(expectation)

    def discard(self, expectation):
        for i, existing in enumerate(self.expectations_with_arguments):
            if existing is expectation:
                del self.expectations_with_arguments[i]
                return
        for i, existing in enumerate(self.expectations_without_arguments):
            if existing is expectation:
                del self.expectations_without_arguments[i]
                return

    def discard_all(self):
        self._remove_method()

    def run(self, args, kw):
        for expectation in self.expectations_with_arguments:
            if expectation.matches(args, kw):
                return expectation.run(args, kw)
        if self.expectations_without_arguments:
            last_set_expectation = self.expectations_without_arguments[-1]
            return last_set_expectation.run(args, kw)
        raise UnexpectedCallError

    def is_satisfied(self):
        for expectation in self._all_expectations():
            if not expectation.satisfied:
                return False
        return True

    def __nonzero__(self):
        return bool(self.expectations_with_arguments or
                    self.expectations_without_arguments)

    def _add_method(self):
        def fn(instance, *args, **kw):
            return self.run(args, kw)
        fn.__name__ = self.method_name
        setattr(self.instance.__class__, self.method_name, fn)

    def _remove_method(self):
        delattr(self.instance.__class__, self.method_name)

    def _add_expectation_with_arguments(self, expectation):
        for i, existing in enumerate(self.expectations_with_arguments):
            if existing.arguments == expectation.arguments:
                self.expectations_with_arguments[i] = expectation
                break
        else:
            self.expectations_with_arguments.append(expectation)

    def _all_expectations(self):
        for expectation in self.expectations_with_arguments:
            yield expectation
        for expectation in self.expectations_without_arguments:
            yield expectation


class BasicStub(object):

    arguments = ExpectationArguments((), {})
    skip_arguments_verification = True
    output_value = None

    def and_return(self, value):
        self.output_value = value
        return self

    def and_yield(self, *args):
        if len(args) == 1:
            self.output = args[0]
        else:
            self.output = lambda *a, **kw: iter(args)
        return self

    def and_raise(self, exception):
        def fn(*args, **kw): raise exception
        self.output = fn
        return self

    def with_args(self, *args, **kw):
        self.skip_arguments_verification = False
        self.arguments = ExpectationArguments(args, kw)
        return self

    def with_kwargs(self, kw):
        self.skip_arguments_verification = False
        self.arguments.kwargs = kw
        return self

    def matches(self, args, kw):
        if self.skip_arguments_verification:
            return True
        return self.arguments == ExpectationArguments(args, kw)

    def run(self, args, kw):
        return self.output(*args, **kw)

    def output(self, *args, **kw):
        return self.output_value

    @property
    def with_any_args(self):
        self.skip_arguments_verification = True
        return self

    @property
    def to_be_called(self):
        return self


class MethodStub(BasicStub):

    def __init__(self, instance, method_name):
        self.instance = instance
        self.method_name = self.__name__ = method_name

    def with_args(self, *args, **kw):
        result = super(MethodStub, self).with_args(*args, **kw)
        self._reorder_expectations()
        return result

    def with_kwargs(self, kw):
        result = super(MethodStub, self).with_kwargs(kw)
        self._reorder_expectations()
        return result

    @property
    def with_any_args(self):
        result = super(MethodStub, self).with_any_args()
        self._reorder_expectations()
        return result

    @property
    def to_be_called(self):
        return self

    def __call__(self):
        return self

    def __str__(self):
        return "<%s for %r on %r>" % (self.__class__.__name__,
                                      self.method_name,
                                      self.instance)

    def set(self):
        expectations = self.instance._expectations_[self.method_name]
        expectations.add(self)

    def unset(self):
        expectations = self.instance._expectations_[self.method_name]
        expectations.discard(self)

    def _reorder_expectations(self):
        expectations = self.instance._expectations_[self.method_name]
        expectations.discard(self)
        expectations.add(self)


class MethodExpectation(MethodStub):

    def __init__(self, instance, method_name):
        super(MethodExpectation, self).__init__(instance, method_name)
        self.satisfied = False
        self.min_calls = self.max_calls = None
        self.limit_calls = True
        self.fail_if_called = False
        self.calls = 0

    def exactly(self, times):
        self.min_calls = self.max_calls = times
        return self

    def at_least(self, times):
        self.min_calls = times
        return self

    def at_most(self, times):
        self.max_calls = times
        return self

    @property
    def ordered(self):
        raise NotImplementedError

    @property
    def to_not_be_called(self):
        raise NotImplementedError

    @property
    def any_number_of_times(self):
        self.min_calls = None
        self.max_calls = None
        self.limit_calls = False
        return self

    @property
    def once(self):
        return self.exactly(1).time

    @property
    def twice(self):
        return self.exactly(2).times

    @property
    def time(self):
        return self

    @property
    def times(self):
        return self

    def run(self, args, kw):
        if self.limit_calls:
            self._ensure_limits_of_calls_are_set()
        self.calls += 1
        if self.max_calls is None or self.calls <= self.max_calls:
            if self.min_calls is None or self.calls >= self.min_calls:
                self.satisfied = True
            return self.output(*args, **kw)
        raise ExpectationNotSatisfiedError

    def _ensure_limits_of_calls_are_set(self):
        if self.min_calls is None and self.max_calls is None: self.once


class InstanceExpectationsContainer(object):
    def __init__(self):
        self._instances = set()

    def add(self, instance):
        self._instances.add(instance)

    def clear(self):
        self._instances = set()

    def __len__(self):
        return len(self._instances)

    def __iter__(self):
        for instance in self._instances:
            yield instance._expectations_


_instances_with_expectations = InstanceExpectationsContainer()
