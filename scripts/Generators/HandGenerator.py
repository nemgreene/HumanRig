import pymel.core as pmc
from pymel.core.datatypes import Vector

import Dictionary
reload(Dictionary)

d = Dictionary

# List of all 
execution1 = "Standard"
execution2 = "Advanced"

executionThreads = [execution1, execution2]


def convertHands(armJoints, side, bs):
    '''Called in the guide extraction phase if hands are required'''
    # offset done by convertHand function duplicated here
    handJoints = {}

    # find furthest extent of fingers
    
    bound = (armJoints[d.j_wrist] - armJoints[d.j_elbow]) + armJoints[d.j_wrist]
    bound = Vector(bound.x, bound.y, armJoints[d.j_wrist].z)
    newWristPosition = armJoints[d.j_wrist]
    indexTip = Vector(bound.x, bound.y, newWristPosition.z)


    # width of the palm
    width =Vector(newWristPosition-Vector(bs.midpoint(indexTip, newWristPosition))).length()
    
    lengthMult = -1 if side == "left" else 1

    # create finger chain
    for name in zip(d.j_fingers, [-.5, -.25, 0, .25, .5]):

        # make joints in the finger
        offsetVector = Vector(abs(name[1]) * lengthMult * (width/2), 1, name[1] * width)

        kD = indexTip + offsetVector
        kA = Vector(bs.midpoint(indexTip, newWristPosition)) + offsetVector
        kB = Vector(bs.midpoint(kD, kA))

        kC = Vector(bs.midpoint(kD, kB))
        
        pmc.select(cl=1)
        label = side.capitalize()
        handJoints[ bs.ng(name[0], label, "KnuckleA")] = bs.makeNested(pmc.joint(n = bs.ng(name[0], label, "KnuckleA"), p = kA,))
        handJoints[ bs.ng(name[0], label, "KnuckleB")] = pmc.joint(n = bs.ng(name[0], label, "KnuckleB"), p = kB,)
        handJoints[ bs.ng(name[0], label, "KnuckleC")] =pmc.joint(n = bs.ng(name[0], label, "KnuckleC"), p = kC,)
        if(name[0] != "Thumb"):
            handJoints[ bs.ng(name[0], label, "KnuckleD")] = pmc.joint(n = bs.ng(name[0], label, "KnuckleD"), p = kD,)

        # slight rotation to show finger orientation
        pmc.rotate(pmc.select(bs.ng(name[0], label, "Knuckle*")), [0, 0, -10 if side == "left" else 10], r=1)

        for joint in handJoints:
            bs.joints[joint] = joint
            bs.guides[joint] = pmc.xform(joint, q=1,  ws=1, t=1)
        
    return

def mirrorHandsBasic(data, leftToRight = True, driverSide="", drivenSide = ""):
# Mirror hands
    for finger in d.j_fingers:
        drivenJoints = data.bs.ng(finger, drivenSide, "KnuckleA*", n=0)
        driverJoints = data.bs.ng(finger, driverSide, "KnuckleA*", n=0)
        pmc.delete(drivenJoints)
        pmc.mirrorJoint(driverJoints, myz=1, mb=1, sr=[driverSide, drivenSide])
  

    # update joint location
    handJoints = filter(lambda x : drivenSide in x and "Knuckle" in x, data.bs.joints)
    for handJoint in handJoints:
        data.bs.joints[handJoint] = pmc.xform(handJoint, q=1, ws=1, t=1)

def mirrorHands(data, leftToRight = True, driverSide="", drivenSide = ""):

    key = ""
    try:
        assert data.bs.input[d.chain_hands]['variation']
        key = data.bs.input[d.chain_hands]['variation']
    except:
        key = execution1
    
    # run selected mirror hands function if multiple are necessary
    executionDict[key](data, leftToRight, driverSide, drivenSide)
    
        

executionDict = {
    execution1 : mirrorHandsBasic,
    execution2 : mirrorHandsBasic
}
