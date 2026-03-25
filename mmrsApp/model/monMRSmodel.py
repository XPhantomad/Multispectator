"""Definition of meta model 'monMRSmodel'."""
from functools import partial
import pyecore.ecore as Ecore
from pyecore.ecore import *


name = 'monMRSmodel'
nsURI = 'http://www.example.org/monMRSmodel'
nsPrefix = 'monMRSmodel'

eClass = EPackage(name=name, nsURI=nsURI, nsPrefix=nsPrefix)

eClassifiers = {}
getEClassifier = partial(Ecore.getEClassifier, searchspace=eClassifiers)


class Model(EObject, metaclass=MetaEClass):

    object = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)
    perceivedrobot = EReference(ordered=True, unique=True,
                                containment=True, derived=False, upper=-1)
    robot = EReference(ordered=True, unique=True, containment=True, derived=False, upper=-1)

    def __init__(self, object=None, perceivedrobot=None, robot=None):
        # if kwargs:
        #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if object:
            self.object.extend(object)

        if perceivedrobot:
            self.perceivedrobot.extend(perceivedrobot)

        if robot:
            self.robot.extend(robot)

    def getobject(self):
        if (self.object != None and self.object != []):
            names = []
            for item in self.object:
                names.append(item.getname())
            return names
        else:
            return None

    def getperceivedrobot(self):
        if (self.perceivedrobot != None and self.perceivedrobot != []):
            names = []
            for item in self.perceivedrobot:
                names.append(item.getname())
            return names
        else:
            return None

    def getrobot(self):
        if (self.robot != None and self.robot != []):
            names = []
            for item in self.robot:
                names.append(item.getname())
            return names
        else:
            return None


class Robot(EObject, metaclass=MetaEClass):

    xPos = EAttribute(eType=EDouble, unique=True, derived=False, changeable=True)
    yPos = EAttribute(eType=EDouble, unique=True, derived=False, changeable=True)
    name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    ip = EAttribute(eType=EInt, unique=True, derived=False, changeable=True)
    perceivedrobot = EReference(ordered=True, unique=True, containment=False, derived=False)

    def __init__(self, xPos=None, yPos=None, name=None, perceivedrobot=None, ip=None):
        # if kwargs:
        #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if xPos is not None:
            self.xPos = xPos

        if yPos is not None:
            self.yPos = yPos

        if name is not None:
            self.name = name

        if ip is not None:
            self.ip = ip

        if perceivedrobot is not None:
            self.perceivedrobot = perceivedrobot

    def getxPos(self):
        return self.xPos

    def getyPos(self):
        return self.yPos

    def getname(self):
        return self.name

    def getip(self):
        return self.ip

    def getperceivedrobot(self):
        if (self.perceivedrobot != None):
            return self.perceivedrobot.getname()
        else:
            return None


class PerceivedRobot(EObject, metaclass=MetaEClass):

    xPos = EAttribute(eType=EDouble, unique=True, derived=False, changeable=True)
    yPos = EAttribute(eType=EDouble, unique=True, derived=False, changeable=True)
    name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    objectGripped = EReference(ordered=True, unique=True, containment=False, derived=False)

    def __init__(self, xPos=None, yPos=None, name=None, objectGripped=None):
        # if kwargs:
        #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if xPos is not None:
            self.xPos = xPos

        if yPos is not None:
            self.yPos = yPos

        if name is not None:
            self.name = name

        if objectGripped is not None:
            self.objectGripped = objectGripped

    def getxPos(self):
        return self.xPos

    def getyPos(self):
        return self.yPos

    def getname(self):
        return self.name

    def getobjectGripped(self):
        if (self.objectGripped != None):
            return self.objectGripped.getname()
        else:
            return None


class Object(EObject, metaclass=MetaEClass):

    name = EAttribute(eType=EString, unique=True, derived=False, changeable=True)
    xPos = EAttribute(eType=EDouble, unique=True, derived=False, changeable=True)
    yPos = EAttribute(eType=EDouble, unique=True, derived=False, changeable=True)

    def __init__(self, name=None, xPos=None, yPos=None):
        # if kwargs:
        #    raise AttributeError('unexpected arguments: {}'.format(kwargs))

        super().__init__()

        if name is not None:
            self.name = name

        if xPos is not None:
            self.xPos = xPos

        if yPos is not None:
            self.yPos = yPos

    def getname(self):
        return self.name

    def getxPos(self):
        return self.xPos

    def getyPos(self):
        return self.yPos
