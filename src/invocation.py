import matchers
import static_mocker

_RETURNS_ = 1
_THROWS_ = 2

class Invocation(object):
  def __init__(self, mock, method_name):
    self.method_name = method_name
    self.mock = mock
    self.verified = False
    self.params = ()
    self.answers = []
    
  def __repr__(self):
    return self.method_name + str(self.params)   
  
class MatchingInvocation(Invocation):
   
  def matches(self, invocation):
    if self.method_name != invocation.method_name:
      return False
    if len(self.params) != len(invocation.params):
      return False
    
    for x, p1 in enumerate(self.params):
      p2 = invocation.params[x]
      if isinstance(p1, matchers.Matcher):
        if not p1.matches(p2): return False
      elif p1 != p2: return False
    
    return True
  
class RememberedInvocation(Invocation):
  def __call__(self, *params, **named_params):
    self.params = params
    self.mock.remember(self)
    
    for matching_invocation in self.mock.stubbed_invocations:
      if matching_invocation.matches(self):
        #TODO LoD    
        return matching_invocation.answers[0].answer()
    
    return None

class VerifiableInvocation(MatchingInvocation):
  def __call__(self, *params, **named_params):
    self.params = params
    matches = 0
    for invocation in self.mock.invocations:
      if self.matches(invocation):
        matches += 1
        invocation.verified = True

    verification = self.mock.pullVerification()
    verification.verify(self, matches)
  
class StubbedInvocation(MatchingInvocation):
  def __call__(self, *params, **named_params):
    self.params = params    
    return AnswerSelector(self)
  
  def stubWith(self, answer, chained_mode):
    if chained_mode:
        self.answers[-1].append(answer.current())
    else:
        self.answers.append(answer)
        
    static_mocker.INSTANCE.stub(self)
    self.mock.finishStubbing(self)
    
  def getOriginalMethod(self):
    return self.mock.mocked_obj.__dict__.get(self.method_name)
  
  def replaceMethod(self, new_method):
    setattr(self.mock.mocked_obj, self.method_name, new_method)  
    
class AnswerSelector:
  def __init__(self, invocation):
    self.invocation = invocation
    self.chained_mode = False
    
  def thenReturn(self, return_value):
    return self.__then(Answer(return_value, _RETURNS_))
    
  def thenRaise(self, exception):
    return self.__then(Answer(exception, _THROWS_))

  def __then(self, answer):
    self.invocation.stubWith(answer, self.chained_mode)     
    self.chained_mode = True
    return self      

class Answer:
  def __init__(self, value, type):
    self.answers = [[value, type]]
    self.index = 0

  def current(self):
    return self.answers[self.index]

  def append(self, answer):
    self.answers.append(answer)

  def answer(self):
    answer, type = self.current() 
    if self.index < len(self.answers) - 1: self.index += 1
    if type == _THROWS_: raise answer
    return answer