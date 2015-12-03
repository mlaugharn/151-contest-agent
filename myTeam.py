# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from captureAgents import CaptureAgent
import random, time, util
from game import Directions
import game
import pprint, math

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'MarcAgent', second = 'MarcAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]
  #return [eval(first), eval(second)]

##########
# Agents #
##########

class DummyAgent(CaptureAgent):
  """
  A Dummy agent to serve as an example of the necessary agent structure.
  You should look at baselineTeam.py for more details about how to
  create an agent as this is the bare minimum.
  """

  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).

    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)

    IMPORTANT: This method may run for at most 15 seconds.
    """

    '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
    CaptureAgent.registerInitialState(self, gameState)

    '''
    Your initialization code goes here, if you need any.
    '''


  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    actions = gameState.getLegalActions(self.index)

    '''
    You should change this in your own agent.
    '''

    return random.choice(actions)

class MarcAgent(CaptureAgent):
  def score(self, **args):
    s = 0
    for feature in self.features:
      if feature in args:
        f = self.features[feature]
        correcting_weight = 1
        s += f(args[feature]) * correcting_weight# * self.corrections[feature]
        #self.corrections[feature] = f(args[feature]) * correcting_weight
        print ">> {}: {}".format(feature, f(args[feature]) * correcting_weight)
    return s

  def hunger_score(self, args):
    gameState, pos, their_food = args
    s = 0
    for food in their_food:
      s += (100./(10 ** (1+ 10./(self.distancer.getDistance(food, pos)) + 1)))**2
    return s

  def near_food(self, args):
    successor, pos, their_food = args
    dist = lambda food: self.getMazeDistance(pos, food)
    closest_food = min(their_food, key = dist)
    if dist(closest_food) == 0: return 10000
    return (10. / (1+dist(closest_food)))**2

  def curl_score(self, args):
    pos, moment = args
    #return (pos[0] * moment[0] + pos[1] * moment[1])
    return 0

  def foodavg(self, args):
    return (10./len(args[1])+1)**5

  def registerInitialState(self, gameState):
    self.visited = util.Counter()
    self.visited_food = set()
    self.moment = None
    self.features = {
    'bias': lambda *args: -1000,
    'explore': lambda pos: (100./(1+self.visited[pos]))**3,
    'score': lambda score: score**3,
    'volatility': lambda winning: winning * random.randint(-100, 100) + random.randint(0,100) * random.randint(1, 5)**(random.random()+.5),
    'hungry': self.hunger_score,
    'near_food': self.near_food,
    "curl": self.curl_score,
    "dontstop": lambda x: 500*(x if x else -10),
    "foodavg": self.foodavg,
    "defensive": lambda (my_food, my_caps): len(my_food)**3
    }
    self.corrections = {}
    self.age = 0
    self.lastsal = None
    CaptureAgent.registerInitialState(self, gameState)
  
  def chooseAction(self, gameState):
    actions = gameState.getLegalActions(self.index)
    choices = {action: None for action in actions}
    
    for action in actions:
      successor = gameState.generateSuccessor(self.index, action)
      state = successor.getAgentState(self.index)
      pos = state.getPosition()
      their_food = self.getFood(successor).asList()
      my_food = self.getFoodYouAreDefending(successor).asList()
      their_caps = self.getCapsules(successor)
      my_caps = self.getCapsulesYouAreDefending(successor)
      score = self.getScore(successor)
      bias = 1
      winning = score > 0
      if self.moment == None: self.moment = pos
      experience = {
        "bias": None,
        "explore": pos,
        "score": score,
        "volatility": winning,
        "hungry": (successor, pos, their_food),
        "near_food": (successor, pos, their_food),
        "cunning": their_caps,
        "defensive": (my_food, my_caps),
        "home": state,
        "curl": (pos, self.moment),
        "dontstop": action != 'Stop',
        "foodavg": (pos, their_food)
      }
      salience = self.score(**experience)
      self.visited[pos] += 1
      choices[action] = salience
      print "{}: {}".format(action, salience)
    maxsal = max(choices.iteritems(), key = lambda (action, score): score)
    for score in choices.itervalues():
      m,n = max(choices.itervalues()), min(choices.itervalues())
      m,n = float(m), float(n)
      self.debugDraw([pos], [.2+50*math.log(score-n + 1, 10000)/(m-n), 0, 0], clear=False)
    #print maxsal
    #pprint.pprint(choices)
    self.age += 1
    pos = gameState.generateSuccessor(self.index, maxsal[0]).getAgentState(self.index).getPosition()
    self.moment = (pos[0] + self.moment[0] / self.age**2, pos[1] + self.moment[1] / self.age**2)
    return maxsal[0]
