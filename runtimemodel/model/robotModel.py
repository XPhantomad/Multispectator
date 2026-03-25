"""Definition of meta model 'robotModel'."""
from functools import partial
import pyecore.ecore as Ecore
from pyecore.ecore import *


name = 'robotModel'
nsURI = 'http://www.example.org/robotModel'
nsPrefix = 'robotModel'

eClass = EPackage(name=name, nsURI=nsURI, nsPrefix=nsPrefix)

eClassifiers = {}
getEClassifier = partial(Ecore.getEClassifier, searchspace=eClassifiers)


class Model(EObject, metaclass=MetaEClass):

    robots = EReference(ordered=True, unique=True, containment=True, derived=False)
    states = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)
    messages = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)

    def __init__(self, robots=None, states=None, messages=None):
        # if kwargs:
        #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if robots is not None:
            self.robots = robots

        if states:
            self.states.extend(states)

        if messages:
            self.messages.extend(messages)

    def getrobots(self):
        if (self.robots != None):
            return self.robots.getname()
        else:
            return None

    def getstates(self):
        if (self.states != None and self.states != []):
            names = []
            for item in self.states:
                names.append(item.getname())
            return names
        else:
            return None

    def getmessages(self):
        if (self.messages != None and self.messages != []):
            names = []
            for item in self.messages:
                names.append(item.getname())
            return names
        else:
            return None


class Robot(EObject, metaclass=MetaEClass):

    xPos = EAttribute(eType=EDouble, unique=True, derived=False, changeable=True)
    yPos = EAttribute(eType=EDouble, unique=True, derived=False, changeable=True)
    zPos = EAttribute(eType=EDouble, unique=True, derived=False, changeable=True)
    id = EAttribute(eType=EInt, unique=True, derived=False, changeable=True, iD=True)
    name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    xTarget = EAttribute(eType=EDouble, unique=True, derived=False, changeable=True)
    yTarget = EAttribute(eType=EDouble, unique=True, derived=False, changeable=True)
    goalReached = EAttribute(eType=EBoolean, unique=True, derived=False, changeable=True)
    theta = EAttribute(eType=EDouble, unique=True, derived=False, changeable=True)
    speed = EAttribute(eType=EDouble, unique=True, derived=False, changeable=True)
    rotationSpeed = EAttribute(eType=EDouble, unique=True, derived=False, changeable=True)
    load = EAttribute(eType=EBoolean, unique=True, derived=False, changeable=True)
    proximity = EAttribute(eType=EBoolean, unique=True, derived=False, changeable=True)
    state = EReference(ordered=True, unique=True, containment=False, derived=False)
    message = EReference(ordered=True, unique=True, containment=False, derived=False)

    def __init__(self, xPos=None, yPos=None, zPos=None, id=None, name=None, xTarget=None, yTarget=None, goalReached=None, theta=None, state=None, speed=None, rotationSpeed=None, load=None, proximity=None, message=None):
        # if kwargs:
        #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if xPos is not None:
            self.xPos = xPos

        if yPos is not None:
            self.yPos = yPos

        if zPos is not None:
            self.zPos = zPos

        if id is not None:
            self.id = id

        if name is not None:
            self.name = name

        if xTarget is not None:
            self.xTarget = xTarget

        if yTarget is not None:
            self.yTarget = yTarget

        if goalReached is not None:
            self.goalReached = goalReached

        if theta is not None:
            self.theta = theta

        if speed is not None:
            self.speed = speed

        if rotationSpeed is not None:
            self.rotationSpeed = rotationSpeed

        if load is not None:
            self.load = load

        if proximity is not None:
            self.proximity = proximity

        if state is not None:
            self.state = state

        if message is not None:
            self.message = message

    def getxPos(self):
        return self.xPos

    def getyPos(self):
        return self.yPos

    def getzPos(self):
        return self.zPos

    def getid(self):
        return self.id

    def getname(self):
        return self.name

    def getxTarget(self):
        return self.xTarget

    def getyTarget(self):
        return self.yTarget

    def getgoalReached(self):
        return self.goalReached

    def gettheta(self):
        return self.theta

    def getspeed(self):
        return self.speed

    def getrotationSpeed(self):
        return self.rotationSpeed

    def getload(self):
        return self.load

    def getproximity(self):
        return self.proximity

    def getstate(self):
        if (self.state != None):
            return self.state.getname()
        else:
            return None

    def getmessage(self):
        if (self.message != None):
            return self.message.getname()
        else:
            return None


class State(EObject, metaclass=MetaEClass):

    id = EAttribute(eType=EInt, unique=True, derived=False, changeable=True, iD=True)
    name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    speedFactor = EAttribute(eType=EDouble, unique=True, derived=False, changeable=True)
    grip = EAttribute(eType=EBoolean, unique=True, derived=False, changeable=True)
    release = EAttribute(eType=EBoolean, unique=True, derived=False, changeable=True)

    def __init__(self, id=None, name=None, speedFactor=None, grip=None, release=None):
        # if kwargs:
        #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if id is not None:
            self.id = id

        if name is not None:
            self.name = name

        if speedFactor is not None:
            self.speedFactor = speedFactor

        if grip is not None:
            self.grip = grip

        if release is not None:
            self.release = release

    def getid(self):
        return self.id

    def getname(self):
        return self.name

    def getspeedFactor(self):
        return self.speedFactor

    def getgrip(self):
        return self.grip

    def getrelease(self):
        return self.release


class Message(EObject, metaclass=MetaEClass):

    id = EAttribute(eType=EInt, unique=True, derived=False, changeable=True, iD=True)
    name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    ledColor = EAttribute(eType=EString, unique=True, derived=False, changeable=True)

    def __init__(self, id=None, name=None, ledColor=None):
        # if kwargs:
        #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if id is not None:
            self.id = id

        if name is not None:
            self.name = name

        if ledColor is not None:
            self.ledColor = ledColor

    def getid(self):
        return self.id

    def getname(self):
        return self.name

    def getledColor(self):
        return self.ledColor
