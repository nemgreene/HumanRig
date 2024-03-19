import pymel.core as pmc
from pymel.core.datatypes import Vector

import Dictionary
import IKFK

reload(Dictionary)
reload(IKFK)

d = Dictionary

# List of all 
execution1 = "Standard"
execution2 = "Custom"

executionThreads = [execution1, execution2]

def __generateSecondaryGuides__1(bs):
    '''No secondary guides required for basic arm rig'''
    pass
def __generateSecondaryGuides__2(bs):
    '''No secondary guides required for advanced arm rig'''
    pass

def __generateRig_1(bs):
    print("Generating arm rig Standard")
def __generateRig_2(bs):
    '''Secondary guides will include a plane to visualize the IK orientation, and a     
    dobule joint along the elbow if required'''
    bs.input[d.chain_arms]["settings"][d.s_doubleJointed]  = False
    # verify all 
        # all joints that the shoulder rig needs
    armJoint = [d.j_elbow, "Shoulder",  d.j_wrist]

    # Verify all joints are present
    try:
        d.verifyJointDependencies(bs, lateralJoints=armJoint)
    except Exception as error:
        print(error, d.chain_arms)
        return
    # Create a rig :)
    
    #Make hierarchy  
    bs.makeNesting([{d.g_armsDynamic: [d.g_armsJoints, d.g_armsCCs]}, {d.g_armsStatic: [d.g_armsMisc] }])

    
    # Find the vector from leftshoulder to leftwrist
    for side in [d.s_Left, d.s_Right]:
        shoulderName = d.j_leftArmName if side == d.s_Left else d.j_rightArmName
        shoulderPos = Vector(bs.guides[shoulderName])
        wristPos = Vector(bs.guides[side + d.j_wrist])
        elbowPos = Vector(bs.guides[side + d.j_elbow])

        offset = (wristPos - shoulderPos ) * d.p_doubleJointMultiplier

        shoulderName = d.jtName(d.j_shoulderName, side = side)
        dAName = d.jtName(d.j_elbowA, side = side)
        dBName = d.jtName(d.j_elbowB, side = side)
        wristName = d.jtName(d.j_wrist, side = side)
        names = [d.j_shoulderName,d.j_elbowA,d.j_wrist]

        if(side == d.s_Left):
        # calculate up vector
            qR = Vector(wristPos-shoulderPos)
            qS = Vector(elbowPos-shoulderPos)
            n = (qR.cross(qS)) * .1
            jts = []
            # make joints
            try:
                # OPTME Why does this dictionary lookup not work?
                # if(bs.input[d.chain_arms]["settings"][d.s_doubleJointed]):
                if(bs.input[d.chain_arms]["settings"][d.s_doubleJointed]):
                    jt1 = bs.makeNested(pmc.joint(n=shoulderName, p=shoulderPos), parent=bs.groups[d.g_armsJoints])
                    jt2= bs.makeNested(pmc.joint(n=dAName, p =  elbowPos + offset * -1))
                    jt3 =bs.makeNested( pmc.joint(n=dBName, p =  elbowPos + offset * 1))
                    jt4 =bs.makeNested( pmc.joint(n=wristName, p =  wristPos))
                    jts = [jt1, jt2, jt3, jt4]
                    names.insert(2, d.j_elbowB)
                else: raise error
            except Exception as error:
                    jt1 = bs.makeNested(pmc.joint(n=shoulderName, p=shoulderPos), parent=bs.groups[d.g_armsJoints])
                    jt2= bs.makeNested(pmc.joint(n=dAName, p =  elbowPos))
                    jt3 =bs.makeNested( pmc.joint(n=dBName, p =  wristPos))
                    jts = [jt1, jt2, jt3]
            # d.update__GuidesAndJoint(bs, shoulderName, jt1)
            # d.update__GuidesAndJoint(bs, dAName, jt2)
            # d.update__GuidesAndJoint(bs, dBName, jt3)
            # d.update__GuidesAndJoint(bs, wristName, jt4)


            # aim joints at children/upVector
            for index, joint in enumerate(jts):
                # for all jts that are not the end joint, aim towards child
                # Up vector for joint is a space locator. Moved along the normal of the plane created by the arm
                if(index < len(jts)-1):
                    loc = bs.makeNested(pmc.spaceLocator(n = "test"))
                    pmc.xform(loc, t=pmc.xform(joint, q=1, ws=1, t=1) + n, )
                    bs.ghostConstraint("aim", jts[index + 1], joint, offset=[0,0,0], weight=1, aimVector=[1,0,0], upVector=[0,1,0], wut="object", wuo=loc)
                    pmc.delete(loc)
                # last jt should be 
                else:
                    bs.ghostConstraint('orient', jts[index-1], joint)
                if(index > 0):
                    pmc.parent(joint, jts[index-1])
            
            # All joints should be in place, create IKFK blend based off input
            # {bs, names : [], side, chain, joints, radiusArr, h_ccs, h_misc, h_joint, h_temp}
            generator_params = d.createContainer()
            generator_params.bs = bs
            generator_params.names = names
            generator_params.targetJts = jts
            generator_params.pvOffset = d.p_armPVOffset
            generator_params.side = side
            generator_params.chain = d.chain_arms
            generator_params.radiusArr = d.p_armsRaduisArr
            generator_params.g_ccs = bs.groups[d.g_armsCCs]
            generator_params.g_joint = bs.groups[d.g_armsJoints]
            generator_params.g_misc = bs.groups[d.g_armsMisc]
            generator_params.g_temp = bs.groups["Temp"]

            ikfk = IKFK.IFKConstructor(generator_params)
            ikfk.execute()
            # this, bs, side, names, joints

        else:
            # Mirror joint chain
            jts = pmc.mirrorJoint(d.jtName(d.j_shoulderName, side = d.s_Left), mirrorYZ=1, mirrorBehavior=1, searchReplace=["_L_", "_R_"])

            generator_params = d.createContainer()
            generator_params.bs = bs
            generator_params.names = names
            generator_params.targetJts = jts
            generator_params.pvOffset = Vector(d.p_armPVOffset) * (1, 1, -1)
            generator_params.side = side
            generator_params.chain = d.chain_arms
            generator_params.radiusArr = d.p_armsRaduisArr
            generator_params.g_ccs = bs.groups[d.g_armsCCs]
            generator_params.g_joint = bs.groups[d.g_armsJoints]
            generator_params.g_misc = bs.groups[d.g_armsMisc]
            generator_params.g_temp = bs.groups["Temp"]

            ikfk = IKFK.IFKConstructor(generator_params)
            ikfk.execute()
            
            # All joints should be in place, create IKFK blend based off input
    


# ----------------------------------------------------Public-----------------------------------------
    
secondaryDict = {
    execution1 : __generateSecondaryGuides__2,
    execution2 : __generateSecondaryGuides__2,
}
executionDict = {
    execution1 : __generateRig_2,
    execution2 : __generateRig_2,
}


def generateFrame(input, refresh = 0):
    # Create initial UI with all variations, hiding all but the first set of options
    
    
    def __toggleProperty(prop):
        try:
            input[d.chain_arms][d.s_settings][prop] = not input[d.chain_arms][d.s_settings][prop]
        except:
            input[d.chain_arms][d.s_settings][prop] = False

        if(prop == d.s_flexiPlane):
            pmc.frameLayout(input['elements'][d.chain_arms][d.s_flexiPlane], e=1, vis = input[d.chain_arms][d.s_settings][d.s_flexiPlane])

    def __updateCount(value, field):
        input[d.chain_arms][d.s_settings][field] = value

    try:
        variation = input[d.chain_arms]['variation']
    except:
        variation = execution2

    if(not refresh):
        input['frames'][d.chain_arms] = {}
        input['elements'][d.chain_arms] = {}
        
        input[d.chain_arms][d.s_settings] ={}
        input[d.chain_arms][d.s_settings][d.s_flexiPlane] = True
        input[d.chain_arms][d.s_settings][d.s_doubleJointed] = True
        input[d.chain_arms][d.s_settings][d.s_IK_FK] = True
        input[d.chain_arms][d.s_settings][d.s_upperFlexiCnt] = d.p_d_upperFlexiCnt
        input[d.chain_arms][d.s_settings][d.s_lowerFlexiCnt] = d.p_d_lowerFlexiCnt

        try:
            ret = pmc.frameLayout()
            with ret:

                customFrame = pmc.frameLayout(visible = False, label = execution2, mh=0)
                with customFrame:
                    with pmc.frameLayout(mw=5, mh=0):
                        with pmc.rowLayout(numberOfColumns=3, columnAttach=[(1, 'both', 0), (2, 'both', 0), (3, 'both', 0)] ):
                            pmc.checkBox(v=1, label = "IKFK", cc= pmc.Callback(lambda : __toggleProperty(d.s_IK_FK)))
                            pmc.checkBox(v=1, label = "Double Jointed", cc= pmc.Callback(lambda : __toggleProperty(d.s_doubleJointed)))
                            pmc.checkBox(v=1, label = "Flexi Plane", cc= pmc.Callback(lambda : __toggleProperty(d.s_flexiPlane)))
                        #     pmc.button(label=execution2)
                        flexiPlaneSettings = pmc.frameLayout(label=d.s_flexiPlane, visible=1)
                        with flexiPlaneSettings:
                            with pmc.rowLayout(numberOfColumns=2 ,  columnAlign2=( 'left', 'left' )):
                                with pmc.rowLayout(numberOfColumns=2):
                                    pmc.text(label = "UpperArm joints")
                                    pmc.intField(ann = "Number of joints in the upper arm Flexiplane", v=d.p_d_upperFlexiCnt,
                                                 minValue=0, maxValue=10, step=1,  cc=lambda x:__updateCount(x,d.s_upperFlexiCnt ))
                                with pmc.rowLayout(numberOfColumns=2):
                                    pmc.text(label = "LowerArm joints")
                                    pmc.intField(ann = "Number of joints in the lower arm Flexiplane", v=d.p_d_lowerFlexiCnt, cc=lambda x:__updateCount(x,d.s_lowerFlexiCnt ))
            
            # stash elements for accessing later
            input['frames'][d.chain_arms][execution2] = customFrame
            input['elements'][d.chain_arms][d.s_flexiPlane] = flexiPlaneSettings

            return ret
        except Exception as error:
            print(error)

    else:
        # This will be called to update the ui on change of value
        # iterate over frames and look for label matching the name 
        frames = input['frames'][d.chain_arms]
        for frame in frames:
            name = pmc.frameLayout(frames[frame], q=1, label=1)
            if(name == variation):
                pmc.frameLayout(frames[frame], edit=1, visible = True)    
                continue
            else:
                pmc.frameLayout(frames[frame], edit=1, visible = False)
                
            
def generateSecondaryGuides(bs):
    key = ""
    try:
        assert bs.input[d.chain_arms]['variation']
        key = bs.input[d.chain_arms]['variation']
    except Exception as error:
        key = execution1
    # run selected mirror hands function if multiple are necessary
    secondaryDict[key](bs)

def generateRig(bs):
    key = ""
    try:
        assert bs.input[d.chain_arms]['variation']
        key = bs.input[d.chain_arms]['variation']
    except Exception as error:
        key = execution1
    
    # run selected mirror hands function if multiple are necessary
    executionDict[key](bs)

