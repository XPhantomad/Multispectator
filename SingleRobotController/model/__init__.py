
from .robotModel import getEClassifier, eClassifiers
from .robotModel import name, nsURI, nsPrefix, eClass
from .robotModel import Model, Robot, State, Message, SUT


from . import robotModel

__all__ = ['Model', 'Robot', 'State', 'Message', 'SUT']

eSubpackages = []
eSuperPackage = None
robotModel.eSubpackages = eSubpackages
robotModel.eSuperPackage = eSuperPackage

Model.robots.eType = Robot
Model.states.eType = State
Model.messages.eType = Message
Model.sut.eType = SUT
Robot.state.eType = State
Robot.message.eType = Message
Robot.sut.eType = SUT

otherClassifiers = []

for classif in otherClassifiers:
    eClassifiers[classif.name] = classif
    classif.ePackage = eClass

for classif in eClassifiers.values():
    eClass.eClassifiers.append(classif.eClass)

for subpack in eSubpackages:
    eClass.eSubpackages.append(subpack.eClass)
