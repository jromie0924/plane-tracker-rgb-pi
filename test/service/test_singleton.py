import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from services.singleton import Singleton


class A(Singleton):
  def __init__(self, initial_value: int = 0):
    if hasattr(self, '_initialized'):
      return
    self._initialized = True
    
    self.value = initial_value

class B(A): pass

class C(Singleton): pass

@pytest.fixture(autouse=True)
def reset():
  A._instance = None # setup
  yield # testing
  A._instance = None # teardown

def test_singleton_multiple_instantiations_results_in_one_instance():
  x = A(10)
  y = A(20) # should be ignored
  assert x is y
  assert x.value == 10
  assert y.value == 10
  
  y.value = 30
  assert x.value == 30
  assert y.value == 30

  assert len(set([x.__class__.__dict__['_instance'], y.__class__.__dict__['_instance']])) == 1

def test_subclasses_get_their_own_instance():
  a = A()
  assert B() is not a
  assert type(B()) is B
  assert C() is not a