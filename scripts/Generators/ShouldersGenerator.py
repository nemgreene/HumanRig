import pymel.core as pmc
from pymel.core.datatypes import Vector

import Dictionary
reload(Dictionary)

d = Dictionary

# List of all 
execution1 = "Standard"
execution2 = "Advanced"

executionThreads = [execution2]

def __generateSecondaryGuides__1(bs):
    def updateCreateLat(shoulderJoint, side, bs ):
        '''Makes/Updates a lat joint secondary guide 1/3 way from shoulder -> lat'''
        shoulderPosition = Vector(bs.guides[shoulderJoint])
        hipPosition = bs.guides[d.j_hipName]
        latPosition = (Vector(hipPosition - shoulderPosition) * .3) + shoulderPosition
        latName = side + d.j_lat

        d.createUpdateJoint(latName, latPosition, bs, secondary = 1)

    def updateCreateTrap(shoulderJoint, side, bs ):
        '''Makes/Updates a trap joint secondary guide equidistant between the shoulder and neckAverage point'''
        shoulderPosition = Vector(bs.guides[shoulderJoint])
        trapPosition = (Vector(bs.neckAveragePosition - shoulderPosition) * .5 ) + shoulderPosition
        trapName = side + d.j_trap


        d.createUpdateJoint(trapName, trapPosition, bs, secondary = 1)

    def updateCreatePec(shoulderJoint, side, bs ):

        '''Calculates a mirrored pair of triangles across the shoulder->clavicle axis, with the pec/neckAverage as the mirrored triangle apexes'''

        shoulderPosition = Vector(bs.guides[shoulderJoint])
        trapPosition = (Vector(bs.neckAveragePosition - shoulderPosition) * .5 ) + shoulderPosition
        claviclePosition = bs.guides[side + d.j_shoulderName ]
        
        clavicleShoulderMidpoint = (Vector(claviclePosition - shoulderPosition) * .5) + shoulderPosition

        pecPosition = (clavicleShoulderMidpoint - trapPosition) + clavicleShoulderMidpoint
        pecName = side + d.j_pec

        d.createUpdateJoint(pecName, pecPosition, bs, secondary = 1)

    def updateCreateScapula(shoulderJoint, side, bs):
        '''Makes/Updates scapA joint secondary guide 1/3 way from shoulder -> opposing shoulder, and adds an arbitrary -z offset'''
        closeShoulder = Vector(bs.guides[shoulderJoint])
        opposingShoulder = Vector(bs.guides[d.j_leftArmName if side == d.s_Right else d.j_rightArmName])

        scapAPosition = (Vector(opposingShoulder-closeShoulder) * .33) + closeShoulder
        # Arbitrary -z axis offfset will be 1/5 of wingspan
        wingSpan = scapAPosition.distanceTo(opposingShoulder)
        scapWidth = wingSpan * -.2
        scapAPosition += Vector(0, 0, scapWidth )
        scapA = side + d.j_scapA

        d.createUpdateJoint(scapA, scapAPosition, bs, secondary =1)
        
        scapB = side + d.j_scapB
        scapBPosition = scapAPosition + Vector(0, scapWidth * 2, 0)
        d.createUpdateJoint(scapB, scapBPosition, bs, secondary =1)
    


    # //find average position of neck joints for the pec/traps calculation
    neckJoints = pmc.ls("*"+ d.j_neckName+"*")
    xCoords = [Vector(pmc.xform(x, q=1, ws=1, t=1)).x for x in neckJoints]
    yCoords = [Vector(pmc.xform(x, q=1, ws=1, t=1)).y for x in neckJoints]
    zCoords = [Vector(pmc.xform(x, q=1, ws=1, t=1)).z for x in neckJoints]

    bs.neckAveragePosition = Vector(sum(xCoords)/len(xCoords), sum(yCoords)/len(yCoords), sum(zCoords)/len(zCoords))

    # add volume joints
    for it in zip([d.j_leftArmName, d.j_rightArmName], [d.s_Left, d.s_Right]):
        pmc.select(cl=1)       
        updateCreateLat(it[0], it[1], bs)
        updateCreateTrap(it[0], it[1], bs)
        updateCreatePec(it[0], it[1], bs)
        updateCreateScapula(it[0], it[1], bs)

def __generateRig_2(bs):
    '''Generate the rig shoulder rig
    This version of the rig is built from a series of aim constraints to support volume maintenance of the trap, lat, and pec, and mimic accurate scapula rotation
    Based off this video https://www.youtube.com/watch?app=desktop&v=9WKbQL8GvWY
    '''
    # all joints that the shoulder rig needs
    pmc.select(cl=1)
    shoulder_unilateral_depJoints = [d.j_lat, d.j_pec, d.j_trap, d.j_scapA, d.j_scapB]
    shoulder_central_depJoints = [d.j_neckName, d.j_hipName]

    # Verify all joints are present
    for side in [d.s_Left, d.s_Right]:
        try:
            assert all(side + x in bs.joints for x in shoulder_unilateral_depJoints)
            assert all(x in bs.joints for x in shoulder_central_depJoints)
        except Exception:
            raise bs.CustomException("Shoulder Rig missing secondary guides")
    
    # Create a rig :)
    
    
    #Make hierarchy  
    bs.makeNesting([{d.g_shoulderDynamic: [d.g_shoulderJoints, d.g_shoulderCCs]}, d.g_shoulderStatic])

    # make "Global move" cc
    shoulderCC = bs.makeNested(pmc.circle(n = d.ng( "cc", "shoulderGlobalMove")), parent = bs.groups[d.g_shoulderCCs])

    d.setColor(shoulderCC[0], d.c_cc_center)

    # getScapB to place the shoulder global move
    scapLeftName, scapRightName  = d.s_Left + d.j_scapB, d.s_Right + d.j_scapB
    y = (Vector(bs.guides[scapLeftName]).y + Vector(bs.guides[scapRightName]).y) /2
    z = (Vector(bs.guides[d.j_leftArmName]).z + Vector(bs.guides[d.j_rightArmName]).z) /2

    # move up between shoulder/scapB
    pmc.xform(shoulderCC, ws=1, a=1, t=Vector(0, y, z), rotation=[90, 0, 0])

    # scale up to approximated size
    wingspan = Vector(bs.guides[d.j_leftArmName]).distanceTo(Vector(bs.guides[d.j_rightArmName]))
    shoulderCC[1].attr("radius").set(wingspan * .66)
    

    # Freeze transforms
    pmc.makeIdentity(shoulderCC, a=1, t=1, r=1, s=1)
    
    # make Locator at neckAverage
    trapLocator = bs.makeNested(pmc.spaceLocator(n = d.ng( "locAlign", "trapDriver"),  ),parent = bs.groups["ShoulderTemp"] )
    pmc.xform(trapLocator, ws=1, a=1, t=bs.neckAveragePosition)

    shoulderLPos, shoulderRPos = [Vector(bs.guides[d.j_leftArmName]),Vector(bs.guides[d.j_rightArmName])]
    spinePos = (shoulderRPos - shoulderLPos) * .5 + shoulderLPos
    spineLocator = bs.makeNested(pmc.spaceLocator(n = d.ng( "locAlign", "scapDriver"),  ),parent = bs.groups["ShoulderTemp"] )


    pmc.xform(spineLocator, ws=1, a=1, t=spinePos)

    # Make unilateral content
    for side in zip([d.s_Left, d.s_Right], [d.j_leftArmName, d.j_rightArmName]):
        sideToggle = side[0] == d.s_Left
        pmc.select(cl=1)
        # make clavicle joints
        clavicleName = n = d.bindName(d.j_shoulderName.lower(), side = side[0])
        claviclePosition = Vector(bs.guides[side[0] + d.j_shoulderName])
        clavicleJoint = bs.makeNested(pmc.joint(n = clavicleName, p = claviclePosition), parent = bs.groups[d.g_shoulderJoints])


        #Make shoulder
        shoulderPosition = Vector(bs.guides[side[1]])
        trapPosition = Vector(bs.guides[side[0] + d.j_trap])

        shoulderBindName = d.bindName(d.bind_shoulder, side = side[0])
        shoulderJoint = pmc.joint(n = shoulderBindName, p = shoulderPosition)


        # Make scapula
        scapAPosition = Vector(bs.guides[side[0] + d.j_scapA])
        scapBPosition = Vector(bs.guides[side[0] + d.j_scapB])


        scapBase = pmc.joint(n = d.ng("jt", d.bind_scapA, side = side[0]), p = shoulderPosition)
        # scapBase = pmc.joint(n = d.jtName(bs, side[0], d.bind_scapA), p = shoulderPosition)
        scapA = pmc.joint(n = d.bindName(d.bind_scapA, side = side[0]), p = scapAPosition)
        pmc.joint(n = d.bindName(d.bind_scapB, side = side[0]), p = scapBPosition)

        # Make Trap
        trapBase = bs.makeNested(pmc.joint(n = d.ng("jt", d.bind_trap, side = side[0]), p = shoulderPosition), parent = shoulderJoint)
        trapJoint = pmc.joint(n = d.bindName(d.bind_trap, side = side[0]), p = trapPosition)

        # either cc should go right under shoulder global move
        ccParent = shoulderCC[0]
        if(side[0] == d.s_Right):
            # or go into a mirror/offset group
            rGrp = bs.makeNested(pmc.group(em=1, n = d.ng( "grpOffset", "shoulder", side = side)), parent = shoulderCC[0])
            pmc.xform(rGrp, a=1, s=(-1,1,1))
            ccParent = rGrp 
        # make ccs
        clavicleCC = bs.makeNested(pmc.curve(n =  d.ng("cc", "shoulder", side = side[0]),d=1,  p = d.arrowPts, k=d.arrowKnots), parent = ccParent)

        # move into place
        bs.ghostConstraint("parent", shoulderJoint, clavicleCC)

        # move the cc up as high as the scapula is tall
        pmc.xform(clavicleCC, r=1, t = (0, scapAPosition.distanceTo(scapBPosition), 0), s = [bs.joint_radius,bs.joint_radius,bs.joint_radius], rotation = [90, 0, 0])
        pmc.makeIdentity(clavicleCC, a=1, t=1, r=1, s=1)

        # color cc accordingly
        d.setColor(clavicleCC, d.colorCCs(side[0]))

        # Control with CCC
        pmc.aimConstraint(clavicleCC, clavicleJoint, mo=1)

        # aim trap at neck
        pmc.aimConstraint(trapLocator, trapBase, mo=1)
        # aim scap at spine driver
        scapAim = pmc.aimConstraint(spineLocator, scapBase, mo=1)

        # Add scap LateralRotation
        pmc.addAttr(clavicleCC, ln="ScapRotation", at="double", k=1)
        pmc.connectAttr(bs.ag(clavicleCC, "ScapRotation"), bs.ag(scapAim, "offsetZ"))
        pmc.connectAttr(bs.ag(clavicleCC, "ScapRotation"), bs.ag(scapAim, "offsetX"))

        scapPos = pmc.xform(scapA, q=1, t=1)

        pmc.addAttr(clavicleCC, ln="ScapSquashDampening", at="enum",en=" ", k=1)

        oMinX = "StartDampeningAngle"
        oMaxX = "EndDampeningAngle"
        minX = "Default_Back_X_Position"
        maxX = "Dampened_Back_X_Postion"

        pmc.addAttr(clavicleCC, ln=minX, at="double", k=1, dv=abs(scapPos[0]))
        pmc.addAttr(clavicleCC, ln=maxX, at="double", k=1, dv=0)
        pmc.addAttr(clavicleCC, ln=oMinX, at="double", k=1, dv=20)
        pmc.addAttr(clavicleCC, ln=oMaxX, at="double", k=1, dv=90)

        # make node chain to add tx to improve scap deformation
        rang = pmc.shadingNode('setRange', au=1, n= d.ng("rang", "scapDriver", side = side[0]))
        cond = pmc.shadingNode('condition', au=1, n= d.ng("cond", "scapDriver", side = side[0]))


        pmc.setAttr(bs.ag(cond, "operation"), 3 if sideToggle else 5)
        pmc.setAttr(bs.ag(cond, "colorIfFalseR"), scapPos[0])

        pmc.connectAttr(bs.ag(clavicleJoint, "rotateY"), bs.ag(rang, "valueX"))
        pmc.connectAttr(bs.ag(clavicleJoint, "rotateY"), bs.ag(cond, "firstTerm"))
        pmc.connectAttr(bs.ag(cond, "outColorR"), bs.ag(scapA, "translateX"))

        if(sideToggle):
            # left side needs to be in negatives to match fields
            multA = pmc.shadingNode("multiplyDivide", au=1, n=d.ng("multA","scapDriverMirror", side=side[0]))
            multB = pmc.shadingNode("multiplyDivide", au=1, n=d.ng("multB","scapDriverMirror", side=side[0]))
            multA.attr("input2").set((-1,-1,-1))
            multB.attr("input2").set((-1,-1,-1))

            pmc.connectAttr(bs.ag(clavicleCC, maxX), bs.ag(rang, "maxX"))
            pmc.connectAttr(bs.ag(clavicleCC, minX), bs.ag(multA, "input1X"))
            pmc.connectAttr(bs.ag(clavicleCC, oMinX), bs.ag(multA, "input1Y"))
            pmc.connectAttr(bs.ag(clavicleCC, oMaxX), bs.ag(multA, "input1Z"))
            pmc.connectAttr(bs.ag(multA, "input1X"), bs.ag(rang, "minX"))
            pmc.connectAttr(bs.ag(multA, "input1Y"), bs.ag(rang, "oldMinX"))
            pmc.connectAttr( bs.ag(multA, "input1Z"), bs.ag(rang, "oldMaxX"))
            pmc.connectAttr(bs.ag(rang, "outValueX"), bs.ag(multB, "input1X"))
            pmc.connectAttr(bs.ag(multB, "outputX"),bs.ag(cond, "colorIfTrueR"))
        else:
            multA = pmc.shadingNode("multiplyDivide", au=1, n=d.ng("multA","scapDriverMirror", side=side[0]))
            multA.attr("input2").set((-1,-1,-1))
            
            pmc.connectAttr(bs.ag(clavicleCC, oMinX), bs.ag(multA, "input1X"))
            pmc.connectAttr(bs.ag(clavicleCC, oMaxX), bs.ag(multA, "input1Z"))

            pmc.connectAttr(bs.ag(clavicleCC, minX), bs.ag(rang, "maxX"))
            pmc.connectAttr(bs.ag(clavicleCC, maxX), bs.ag(rang, "minX"))
            
            pmc.connectAttr(bs.ag(multA, "outputZ"), bs.ag(rang, "oldMinX"))
            pmc.connectAttr(bs.ag(multA, "outputX"), bs.ag(rang, "oldMaxX"))
            pmc.connectAttr(bs.ag(rang, "outValueX"), bs.ag(cond, "colorIfTrueR"))

        bs.attrCleanup(clavicleCC, ["r", "s", "v"])

        pmc.pointConstraint(shoulderCC[0], clavicleJoint, mo=1 )

        pmc.select(cl=1)
        # make pec joint
        pecPosition = Vector(bs.guides[side[0] + d.j_pec])
        pecJoint = bs.makeNested(pmc.joint(n = d.bindName("pecVolume", side = side[0])))
        pmc.xform(pecJoint, ws=1, a=1, t=pecPosition)

        pmc.pointConstraint(shoulderCC, shoulderJoint, pecJoint, mo=1)

        # make lat joint
        latPosition = Vector(bs.guides[side[0] + d.j_lat])
        latJoint = bs.makeNested(pmc.joint(n = d.bindName("latVolume", side = side[0])))
        pmc.xform(latJoint, ws=1, a=1, t=latPosition)
        pmc.pointConstraint(shoulderCC, shoulderJoint, latJoint, mo=1)

    # constrain temps to shoulder move
    pmc.parentConstraint(shoulderCC[0], trapLocator, mo=1 )
    pmc.parentConstraint(shoulderCC[0], spineLocator, mo=1 )
    
    # cleaup rig
    pmc.delete(shoulderCC, ch=1)
    bs.attrCleanup(shoulderCC[0], ["s", "v"])


# ----------------------------------------------------Public-----------------------------------------
    
secondaryDict = {
    execution1 : __generateSecondaryGuides__1,
    execution2 : __generateSecondaryGuides__1,
}
executionDict = {
    execution1 : __generateRig_2,
    execution2 : __generateRig_2,
}

def generateSecondaryGuides(bs):
    key = ""
    try:
        assert bs.inputs[d.chain_shoulders]['variation']
        key = bs.inputs[d.chain_shoulders]['variation']
    except:
        key = execution1
    
    # run selected mirror hands function if multiple are necessary
    secondaryDict[key](bs)

def generateRig(bs):
    key = ""
    try:
        assert bs.inputs[d.chain_shoulders]['variation']
        key = bs.inputs[d.chain_shoulders]['variation']
    except:
        key = execution1
    
    # run selected mirror hands function if multiple are necessary
    executionDict[key](bs)

