
from .monMRSmodel import getEClassifier, eClassifiers
from .monMRSmodel import name, nsURI, nsPrefix, eClass
from .monMRSmodel import Model, Robot, PerceivedRobot, Object


from . import monMRSmodel

__all__ = ['Model', 'Robot', 'PerceivedRobot', 'Object']

eSubpackages = []
eSuperPackage = None
monMRSmodel.eSubpackages = eSubpackages
monMRSmodel.eSuperPackage = eSuperPackage

Model.object.eType = Object
Model.perceivedrobot.eType = PerceivedRobot
Model.robot.eType = Robot
Robot.perceivedrobot.eType = PerceivedRobot
PerceivedRobot.objectGripped.eType = Object

otherClassifiers = []

for classif in otherClassifiers:
    eClassifiers[classif.name] = classif
    classif.ePackage = eClass

for classif in eClassifiers.values():
    eClass.eClassifiers.append(classif.eClass)

for subpack in eSubpackages:
    eClass.eSubpackages.append(subpack.eClass)
