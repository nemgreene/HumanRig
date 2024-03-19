
import pymel.core as pmc
import maya.api.OpenMaya as om
from pymel.core.datatypes import Vector

def createContainer( ):
    """
    This method creates a container object which fields can be assigned
    dynamically.
    
    For instance, the object returned by this method will allow:
    
    obj = createContainer()
    obj.newAttribute = 'my new attribute value'
    """
    
    # Way to create temporary structure.
    return type( 'TempStruct' , ( object , ) , {} )

# UI Data

input = createContainer()
input.foot = True
input.leg = True
input.hips = True
input.spine = True
input.arm = True
input.shoudler = True
input.spineCount = 3

# Expose params
# on mirror, center guides will snap to x 0, else will snap to hips x
p_snapToCenterOnMirror = True
# default flexi plane counts
p_d_upperFlexiCnt = 5
p_d_lowerFlexiCnt = 5
# on double jointing, the joints will be moved alond the length of the bones by (mult * length)
p_doubleJointMultiplier = .01
# IKFK rig tool modifiers for bind, fk, ik joint radius
p_armsRaduisArr = [.5, .3, .1]
# Polve vector offset for the arms
p_armPVOffset = [0,0,-1 ]
# Arbitraty FK cc scale, * bs.joint_radius
p_arm_ccFKScale = 2
# Defualt value for ik?fk on arm
p_arm_IKFKDefault = 1

# the utility function that queries for avg column with for rig creation needs to know the skins name
p_skinName = "Skin2"

# --------------------------------------------------------------------Colors
c_guides_primary = [0,0,1]
c_guides_secondary = [1,0,0]
c_cc_left = [1,0,0]
c_cc_right = [1,1,0]
c_cc_center = [1,0,1]

# -----------------------------------------------------------------Create Guides---------------------------------------------------
# bs.joint_radius

s_Left = "Left"
s_Right = "Right"
j_hipName= "Hips"
j_hipTranslation= "HipsTranslation"
j_spineName= "Spine"
j_neckName = "Neck"
j_headName = "Head"
j_leftArmName = s_Left + "Shoulder"
j_rightArmName = s_Right + "Shoulder"
j_shoulderName = "Clavicle"
j_shoulderExtraName = "ClavicleExtra"
j_knee = "Leg"
j_ankle = "Foot"
j_toeBase = "ToeBase"
j_elbow = "Elbow"
j_wrist = "Wrist"

j_fingers = ['Pinky','Ring', 'Middle', 'Index', 'Thumb' ]

# -----------------------------------------------------------------Secondary Guides------------------------------------------
j_neckAverage = "NeckAverage"
j_trap = "Trap"
j_lat = "Lat"
j_pec = "Pec"
j_scapA = "ScapA"
j_scapB = "ScapB"
j_doubleA = "DoubleA"
j_doubleB = "DoubleB"


# DNI-----------------------------------------------------------------------
e_Left = "left"
e_Right = "right"
e_hips = 'hips' 
e_back = 'back' 
e_shoulders = 'shoulders' 
e_head = 'head' 
e_leftShoulder = e_Left +'_shoulder' 
e_rightShoulder = e_Right + '_shoulder' 
e_thigh = '_thigh'
e_knee = '_knee'
e_ankle = '_ankle'
e_foot = '_foot'
e_elbow = '_elbow'
e_hand = '_hand'

# --------------------------------------------Executuion threads

chain_hips = "hips"
chain_spine = "spine"
chain_head = "head"
chain_neck = "neck"
chain_shoulders = "shoulders"
chain_arms = "arms"
chain_hands = "hands"
chain_legs = "legs"
chain_feet = "feet"

# Any custom frames for the UI will be called in the following namespace
generate_frame = "GenerateFrames"
# Any custom createGudies functions will be called in the following namespace
guides_custom = "CreateGuides"
# Any custom mirror functions will be called in the following namespace
mirror_hands = "MirrorHand"
# Any Secondary Guides will be listed in the following namespace
guides_secondary = "SecondaryGuides"
# All generateRig function should be stored in the following namespace
generate_rig = "GenerateRig"

chains = [chain_hips,chain_spine,chain_head,chain_neck,chain_shoulders,chain_arms,chain_hands,chain_legs,chain_feet]
# ---------------------------------------------------------------------UI Settings
s_settings = "settings"
s_IK_FK = "hasIKFK"
s_doubleJointed = "hasDoubleJointed"
s_flexiPlane = "hasFlexiPlane"
s_upperFlexiCnt = "UpperFlexiCnt"
s_lowerFlexiCnt = "LowerFlexiCnt"
# ----------------------------------------------------------------Connections
'''Certain Chain execution will be dependent on the construction of other guides. 
These need to be linked in the Nexus gnerator'''

chain_required = "chainRequired"
requiredTable = 'requiredTable'
chainRequired = 'chainRequired'

# -------------------------------------------------------------------UI Labels

uil_generateBaseGuides = "1) Generate Guides"
uil_mirrorLtR = "    Symmetrize R <- L    "
uil_mirrorRtL = "    Symmetrize R -> L    "
uil_generateSecondaryGuides = "Generate/Update Secodary Guides"
uil_createRig = "Create Rig from Guides"

# ---------------------------------------------------------------------Hierarchy
# cleanup 
g_globalStatic = "global_static"
g_globalDynamic = "global_dynamic"
g_shoulderStatic = "shoulder_static"
g_shoulderDynamic = "shoulder_dynamic"
g_shoulderJoints = 'jts_shoulder'
g_shoulderCCs = 'ccs_shoulder'
g_armsStatic = "arms_static"
g_armsDynamic = "arms_dynamic"
g_armsJoints = 'jts_arms'
g_armsCCs = 'ccs_arms'
g_armsMisc = 'misc_arms'

# ---------------------------------------------------------------------------------Joints
j_elbowA = "ElbowA"
j_elbowB = "ElbowB"
# ---------------------------------------------------------------------------------Bind Joint
def ng(*args, **kwargs):
    '''type_bs.label_suffix_side_prefix01'''
    side = "" if "side" not in kwargs else kwargs["side"]
    args = list(args)
    args.insert(1, bs.label)
    if(side):
        args.insert(2, "L" if side == s_Left else "R")
    return(bs.ng(*args))
    
def bindName(suff, **kwargs):
    if("side" in kwargs):
        ret = ng("bind", suff, side = kwargs['side'])
        return ret
    ret = ng("bind", suff)
    return ret

def jtName(suff, **kwargs):
    if("side" in kwargs):
        ret = ng("jt", suff, side = kwargs['side'])
        return ret
    ret = ng("jt", suff)
    return ret

def ikName(suff, **kwargs):
    if("side" in kwargs):
        ret = ng("jt_IK", suff, side = kwargs['side'])
        return ret
    ret = ng("jt_IK", suff)
    return ret

def fkName(suff, **kwargs):
    if("side" in kwargs):
        ret = ng("jt_FK", suff, side = kwargs['side'])
        return ret
    ret = ng("jt_FK", suff)
    return ret

bind_shoulder = "shoulder"
bind_trap = "trap"
bind_scapA = "scapA"
bind_scapB = "scapB"
# ---------------------------------------------------------------------------------CCs

arrowPts = [[0, 0, 2],[-1, 0, 0.5],[-0.5, 0, 0.5],[-0.5, 0, -1],[0.5, 0, -1],[0.5, 0, 0.5],[1, 0, 0.5],[0, 0, 2]]
arrowPts = [[x[0], x[1], x[2] - 2] for x in arrowPts]

arrowKnots = [0,1,2,3,4,5,6,7]

def colorCCs(side):
    return c_cc_left if side ==s_Left else c_cc_right

def ccName(*suff,**kwargs):
    ''' d.ccName("globalMove","", "shoulder")'''
    if("side" in kwargs):
        ret = ng("anim", *suff, side = kwargs['side'])
        return ret
    ret = ng("anim", *suff)
    return ret

cc_shoulderGlobalMove = "shoulderGlobalMove"

# --------------------------------------------------------------------------------Utiliteis
def nodeName(*suff, **kwargs):
    if("side" in kwargs):
        ret = ng(*suff, side = kwargs['side'])
        return ret
    ret = ng(*suff)
    return ret



def update__GuidesAndJoint(bs, key, value):
    '''Expects a joint in, finds its world translation, and updates bs'''
    bs.joints[key] = value
    bs.guides[key] = pmc.xform(value, q=1, ws=1, t=1)

def createUpdateJoint(jointName, position, bs, **kwargs):
    '''Either create a joint with the name, or update its position in the world, and update bs.joints/guides'''
    if(jointName in bs.guides):
        bs.guides[jointName] = position
        pmc.xform(bs.joints[jointName], ws=1, a=1, t=position)
    else:
        joint = bs.makeNested(pmc.joint(n = jointName, position = position), parent = bs.guidesRoot if "parent" not in kwargs else kwargs['parent'])
        update__GuidesAndJoint(bs, jointName, joint)

    if("secondary" in kwargs):
        pmc.setAttr(bs.ag(bs.joints[jointName], "overrideEnabled"), 1)
        pmc.setAttr(bs.ag(bs.joints[jointName], "overrideRGBColors"), 1)
        for channel, color in zip(["R", "G", "B"], c_guides_secondary):
            pmc.setAttr(bs.joints[jointName] + ".overrideColor%s" %channel, color)
    if("primary" in kwargs):
        pmc.setAttr(bs.ag(bs.joints[jointName], "overrideEnabled"), 1)
        pmc.setAttr(bs.ag(bs.joints[jointName], "overrideRGBColors"), 1)
        for channel, color in zip(["R", "G", "B"], c_guides_primary):
            pmc.setAttr(bs.joints[jointName] + ".overrideColor%s" %channel, color)
    if("color" in kwargs):
        pmc.setAttr(bs.ag(bs.joints[jointName], "overrideEnabled"), 1)
        pmc.setAttr(bs.ag(bs.joints[jointName], "overrideRGBColors"), 1)
        for channel, color in zip(["R", "G", "B"], color):
            pmc.setAttr(bs.joints[jointName] + ".overrideColor%s" %channel, color)
    return bs.joints[jointName]

def setColor(obj, color):
    pmc.setAttr(obj+ ".overrideEnabled", 1)
    pmc.setAttr(obj+ ".overrideRGBColors", 1)
    for channel, color in zip(["R", "G", "B"], color):
        pmc.setAttr(obj + ".overrideColor%s" %channel, color)

def setCCColorBySide(obj, side = None, ):
    if(not side):
        setColor(obj, c_cc_center)
        return
    if(side == s_Left):
        setColor(obj, c_cc_left)
    if(side == s_Right):
        setColor(obj, c_cc_right)



def verifyJointDependencies(bs, lateralJoints = [], unilateralJoints = []):
    pmc.select(cl=1)
        # Verify all joints are present
    print("checking")
    for side in [s_Left, s_Right]:
        try:
            assert all(side + x in bs.joints for x in lateralJoints)
            assert all(x in bs.joints for x in unilateralJoints)
        except Exception:
            raise bs.CustomException("JointDependency Error")
        
def getColumnRadius(skinName, targ, up = [1, 0, 0]):

        hits = []
        vectors = [[1,0,0], [0,1,0], [0,0,1]]
        vectors = filter(lambda x : x != up, vectors)
        vectors = [Vector(x) for x in vectors]
        vectors += [Vector(x) * -1 for x in vectors]
        
        # Create a list which can hold MObjects, MPlugs, MDagPaths
        selectionList = om.MSelectionList()
        selectionList.add(skinName) # Add mesh to list
        dagPath = selectionList.getDagPath(0) # Path to a DAG node
        fnMesh = om.MFnMesh(dagPath) # Function set for operation on meshes
        position = Vector(pmc.xform(targ, q=1, ws=1, t=1))
        
        for vector in vectors:
            intersection = fnMesh.closestIntersection(
                om.MFloatPoint(position), # raySource
                om.MFloatVector(vector), # rayDirection
                om.MSpace.kWorld, # space
                99999, # maxParam
                False) # testBothDirections

            if(intersection[2]!= -1 and intersection[3] != -1):
                point = intersection[0]
                pos = Vector(point[0], point[1], point[2])
                hits.append(pos)

        if(len(hits) == 4):
            for x in hits:
                pmc.spaceLocator(name = "test", p=x)
            return 1.25* sum([x.distanceTo(position) for x in hits])/4
        else:
            return False
        
def makeCCShape(skinName, targ):

        cvs = pmc.ls(targ + ".cv[*]", fl=1)
        vectors = [Vector(pmc.pointPosition(x, w=1)) for x in cvs]
        hits=[]

        # Create a list which can hold MObjects, MPlugs, MDagPaths
        selectionList = om.MSelectionList()
        selectionList.add(skinName) # Add mesh to list
        dagPath = selectionList.getDagPath(0) # Path to a DAG node
        fnMesh = om.MFnMesh(dagPath) # Function set for operation on meshes
        position = Vector(pmc.xform(targ, q=1, ws=1, t=1))
        
        for vector in vectors:
            multVector = (position - vector) * 10
            intersection = fnMesh.closestIntersection(
                om.MFloatPoint(position), # raySource
                om.MFloatVector(multVector), # rayDirection
                om.MSpace.kWorld, # space
                99999, # maxParam
                False) # testBothDirections
            if(intersection[2]!= -1 and intersection[3] != -1):
                point = intersection[0]
                pos = Vector(point[0], point[1], point[2])
                hits.append(pos)

        if(len(hits) == 8):
            for index, cv in enumerate(cvs):
                hitPosition = hits[index]
                scaled = ((position - hitPosition) * -1.5) + position
                pmc.xform(cv, a=1, t=scaled, ws=1)