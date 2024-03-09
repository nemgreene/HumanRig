import pymel.core as pmc
from pymel.core.datatypes import Vector
import json

import Dictionary
reload(Dictionary)

###############################################################################
#                                                                             #
#  Constants                                                                  #
#                                                                             #
###############################################################################

d =  Dictionary

# Space definition: Up is positive Y, mirror plane is along X axis.
kCharacterSymmetryAxis  = 0
kCharacterDownDirection = 0 # Min corner of bounding box.
kCharacterUpDirection   = 1 # Max corner of bounding box.
kCharacterUpAxis        = 1 # Y direction.

# These are used in the tweaking of the joint placement.
kTweakSpine = True
kTweakSpineFirstRatio = 0.20
kTweakSpineLastRatio  = 0.60
kTweakNeck = True
kTweakNeckFirstRatioNoTweak = 0.4
kTweakNeckFirstRatio        = 0.25
kTweakNeckLastRatio         = 0.45
kTweakShoulder = True
kTweakShoulderRatio = 0.6
kTweakFoot = True
kTweakFootToeRatio                = 0.4
kTweakFootAnkleRatio              = 0.2
kTweakFootUseCorrectedAnkleForToe = False
kTweakHand = True
kTweakHandRatio = 0.4

# Name of the child attribute on the Quick Rig info attribute to store the guides.
kGuidesAttributeName = 'guides'


skeletonParameters = {
    # Center.
    'NeckCount'     : 1,
    'ShoulderCount' : 1,
    'SpineCount'    : 1,
    'WantHipsTranslation' : 1 ,
    }

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



def qrGetDefaultTweakParameters( ):
    """
    This method returns the default tweak parameters for modifying the result
    of the skeletonEmbed command.
    
    At the moment, these are hard-coded, but eventually they should be
    configurable.
    """
    
    tweakParameters = createContainer( )
    
    spine = createContainer( )
    spine.tweak      = kTweakSpine
    spine.firstRatio = kTweakSpineFirstRatio
    spine.lastRatio  = kTweakSpineLastRatio
    # spine.count = 5
    tweakParameters.spine = spine
    
    neck = createContainer( )
    neck.tweak             = kTweakNeck
    neck.firstRatioNoTweak = kTweakNeckFirstRatioNoTweak
    neck.firstRatio        = kTweakNeckFirstRatio
    neck.lastRatio         = kTweakNeckLastRatio
    tweakParameters.neck = neck
    
    shoulder = createContainer( )
    shoulder.tweak = kTweakShoulder
    shoulder.ratio = kTweakShoulderRatio
    tweakParameters.shoulder = shoulder
    
    foot = createContainer( )
    foot.tweak                   = kTweakFoot
    foot.toeRatio                = kTweakFootToeRatio
    foot.ankleRatio              = kTweakFootAnkleRatio
    foot.useCorrectedAnkleForToe = kTweakFootUseCorrectedAnkleForToe
    tweakParameters.foot = foot
    
    hand = createContainer( )
    hand.tweak = kTweakHand
    hand.ratio = kTweakHandRatio
    tweakParameters.hand = hand
    
    return tweakParameters


# IMPME: For now, these are hard-coded values, but there should be a UI for them.
tweakParameters = qrGetDefaultTweakParameters( )



def safeDivide( x , y ):
    """
    Divide two numbers, returning 0 if the divisor is 0.
    """
    return x / y if y else 0

class PieceWiseLinearFunction:
    """
    This class handles interpolation between an array of points.
    """
    
    def __init__( self , points ):
        self.points = points
        
        vectors = [ ]
        for i in range( len( points ) - 1 ):
            vectors.append( points[ i + 1 ] - points[ i ] )
        
        lengths = [ v.length( ) for v in vectors ]
        totalLength = sum( lengths )
        
        self.ratios = [ ]
        currentLength = 0
        for length in lengths:
            self.ratios.append( safeDivide( currentLength , totalLength ) )
            currentLength += length
        self.ratios.append( 1.0 )
    
    def evaluate( self , value ):
        if ( value <= 0 ):
            return self.points[ 0 ]
        elif ( value >= 1 ):
            return self.points[ -1 ]
        else:
            for i in range( len( self.ratios ) ):
                if self.ratios[ i + 1 ] > value:
                    break
            factor0 = self.ratios[ i     ]
            factor1 = self.ratios[ i + 1 ]
            
            factor = safeDivide( value - factor0 , factor1 - factor0 )
            
            return self.points[ i ] * ( 1 - factor ) + self.points[ i + 1 ] * factor


def qrCreateGuidesNode( embedding ):
    """
    This method creates a node in the scene that will store the embedding
    information returned by the skeletonEmbed command.
    
    It will create a root joint to which will be parented one joint for each
    joint in the embedding.  It will also store bounding box information
    as an attribute on that root joint.
    """
    
    # We get all the parameters first, so if some are missing we have an error before we create anything.
    
    # Get the bounding box.
    boundingBox = embedding[ 'boundingBox' ]
    minCorner = boundingBox[ 'min' ]
    maxCorner = boundingBox[ 'max' ]
    # Get the joints / guides.
    skeletonJoints = embedding[ 'guides' ]
    # Get the conversion factor.
    conversionFactorCmToWorld = embedding[ 'conversionFactor' ]
    
    # Create a set of editable nodes in the scene corresponding to the embedding.
    rootJoint = pmc.createNode( 'joint' , name='Root' )
    
    # Add attributes for bounding box.
    for corner in [ 'min' , 'max' ]:
        # Create the attribute.
        attributeName = corner + 'Corner'
        pmc.addAttr( rootJoint , longName=attributeName , attributeType='compound' , numberOfChildren=3 )
        for coord in [ 'X' , 'Y' , 'Z' ]:
            pmc.addAttr( rootJoint , longName=attributeName + coord , attributeType='doubleLinear' , parent=attributeName )
        
        # Set the value.
        value = boundingBox[ corner ]
        pmc.setAttr( '%s.%s' % ( rootJoint , attributeName ) , *value )
    # Use the bounding box of the skeleton as a heuristic to estimate the scale of the joints.
    # Even if world units are not cm, the radius must be in cm.
    distance = ( Vector( minCorner ) - Vector( maxCorner ) ).length( )
    radius = distance * 0.012 / conversionFactorCmToWorld
    
    # Do not display connections to the root.
    pmc.setAttr( '%s.drawStyle' % rootJoint , 2 )
    pmc.setAttr( '%s.displayHandle' % rootJoint , 1 )
    
    # Add attribute for guides.
    pmc.addAttr( rootJoint , longName=kGuidesAttributeName , numberOfChildren=len( skeletonJoints ) , attributeType='compound' )
    for jointName in skeletonJoints:
        pmc.addAttr( rootJoint , longName=jointName , attributeType='message' , parent=kGuidesAttributeName )
    # We arbitrarily create joints in alphabetical order (the order it will show in the outliner).
    # ANSME: Should we create them in hierarchical order instead (parent before children)?
    for jointName in sorted( skeletonJoints ):
        jointPosition = skeletonJoints[ jointName ]
        joint = pmc.createNode( 'joint' , name=jointName )
        parentedJoints = pmc.parent( joint , rootJoint )
        assert( len( parentedJoints ) == 1 )
        parentedJoint = parentedJoints[ 0 ]
        # Set the right position.
        pmc.xform( parentedJoint , worldSpace=True , translation=jointPosition )
        # Connect so it can be retrieved later.
        pmc.connectAttr( '%s.message' % parentedJoint , '%s.%s.%s' % ( rootJoint , kGuidesAttributeName , jointName ) )
        # Scale the size to fit the skeleton size.
        pmc.setAttr( '%s.radius' % parentedJoint , radius )
    
    return rootJoint

def convertReference( minCorner , maxCorner ):
    """
    This method takes the position of bounding box corners and maps them to
    a reference joint that HumanIK expects.
    """
    center = ( minCorner + maxCorner ) * 0.5
    center[ kCharacterUpAxis ] = [ minCorner , maxCorner ][ kCharacterDownDirection ][ kCharacterUpAxis ]
    
    return { 'Reference' : center }

def convertSpine( tweakParameters , spineCount , wantHipsTranslation , hipsPosition , backPosition , shouldersPosition, bs ):
    """
    This method takes the position of the spine guides coming out of the
    embedding algorithm (hips, back and shoulders) and maps them to spine
    joints that fits what HumanIK expects.
    """
    
    spineJoints = {}

    if tweakParameters.tweak:
        spineFunc = PieceWiseLinearFunction( [ hipsPosition , backPosition , shouldersPosition ] )
        firstSpine = spineFunc.evaluate( tweakParameters.firstRatio )
        lastSpine  = spineFunc.evaluate( tweakParameters.lastRatio  )
    else:
        firstSpine = backPosition
        lastSpine  = shouldersPosition
    
    spineJoints[ d.j_hipName ]  = hipsPosition
    spineJoints[ d.j_spineName ] = firstSpine
    numberOfSpineJointsToAdd = spineCount - 2
    if numberOfSpineJointsToAdd == -1:
        # This means that we are done, nothing else to add.
        pass
    else:
        assert( numberOfSpineJointsToAdd >= 0 )
        for i in range( numberOfSpineJointsToAdd + 1 ):
            factor = ( i + 1.0 ) / ( numberOfSpineJointsToAdd + 1.0 )
            position = firstSpine * ( 1 - factor ) + lastSpine * ( factor )
            name = 'Spine%d' % ( i + 1 )
            spineJoints[ name ] = position
    
    if wantHipsTranslation:
        spineJoints[ 'HipsTranslation' ] = hipsPosition
    
    return spineJoints

def convertNeck( tweakParameters , neckCount , shouldersPosition , headPosition , boundingBox ):
    """
    This method takes the position of the neck guides coming out of the
    embedding algorithm (shoulders and neck) and maps them to neck joints that
    fits what HumanIK expects.
    """
    
    neckJoints = {}
    
    if tweakParameters.tweak:
        # Bottom of neck.
        factor = tweakParameters.firstRatio
        firstNeck = shouldersPosition * ( 1 - factor ) + headPosition * ( factor )
        
        # Get the top of the head.
        headTopUp   = boundingBox[ kCharacterUpDirection ][ kCharacterUpAxis ]
        shouldersUp = shouldersPosition[ kCharacterUpAxis ]
        headUp      = headPosition[ kCharacterUpAxis ]
        factor = safeDivide( headTopUp - shouldersUp , headUp - shouldersUp )
        if factor <= 0:
            pmc.warning( "Custom Warning" )
            lastNeck = headPosition
        else:
            headFactor = factor * tweakParameters.lastRatio
            lastNeck = shouldersPosition * ( 1 - headFactor ) + headPosition * headFactor
    else:
        factor = tweakParameters.firstRatioNoTweak
        firstNeck = shouldersPosition * ( 1 - factor ) + headPosition * ( factor )
        lastNeck  = headPosition
    
    for i in range( neckCount ):
        factor = i / float( neckCount )
        position = firstNeck * ( 1 - factor ) + lastNeck * ( factor )
        name = 'Neck%s' % ( str( i ) if i else '' )
        neckJoints[ name ] = position
    neckJoints[ 'Head' ] = lastNeck
    
    return neckJoints

def convertShoulder( tweakParameters , shoulderCount , shouldersPosition , leftShoulderPosition , rightShoulderPosition, bs ):
    """
    This method takes the position of the shoulder guides coming out of the
    embedding algorithm (shoulders and left/right shoulder) and maps them to
    clavicle joints that fits what HumanIK expects.
    """
    # if neither shoulder nor arm selected, abort
    if ((not bs.input['shoulders']['execute']) and (not bs.input['arms']['execute'])):
        return {}
    

    shoulderJoints = {
        'LeftArm'  : leftShoulderPosition  ,
        'RightArm' : rightShoulderPosition ,
    }
    
    if(not bs.input['shoulders']['execute']):
        return shoulderJoints
        

    if tweakParameters.tweak:
        shoulderFactor = tweakParameters.ratio
    else:
        # Fist clavicle is 40% between center of shoulders and shoulder.
        shoulderFactor = 0.4
    
    assert( shoulderCount >= 0 )
    if shoulderCount > 0:
        clavicleNames = [ 'Shoulder' , 'ShoulderExtra' ]
        assert( shoulderCount <= len( clavicleNames ) )
        
        factor = shoulderFactor / 2.0
        leftClaviclePosition  = leftShoulderPosition * ( 1 - factor ) + rightShoulderPosition * ( factor     )
        rightClaviclePosition = leftShoulderPosition * ( factor     ) + rightShoulderPosition * ( 1 - factor )
        shoulderJoints[ 'Left'  + clavicleNames[ 0 ] ] = leftClaviclePosition
        shoulderJoints[ 'Right' + clavicleNames[ 0 ] ] = rightClaviclePosition
        print(bs.input, "Here")
        return shoulderJoints
        for i in range( shoulderCount - 1 ):
            factor = ( i + 1.0 ) / ( shoulderCount )
            
            leftPosition = leftClaviclePosition * ( 1 - factor ) + leftShoulderPosition * ( factor )
            leftName = 'Left' + clavicleNames[ i + 1 ]
            shoulderJoints[ leftName ] = leftPosition
            
            rightPosition = rightClaviclePosition * ( 1 - factor ) + rightShoulderPosition * ( factor )
            rightName = 'Right' + clavicleNames[ i + 1 ]
            shoulderJoints[ rightName ] = rightPosition
    
    return shoulderJoints

def convertFoot( tweakParameters , kneePosition , anklePosition , footPosition ):
    """
    This method takes the position of the foot guides coming out of the
    embedding algorithm (knee, ankle and foot) and maps them to foot joints
    that fits what HumanIK expects.
    """
    
    footJoints = {}
    
    if tweakParameters.tweak:
        kneeUp   = kneePosition [ kCharacterUpAxis ]
        ankleUp  = anklePosition[ kCharacterUpAxis ]
        footUp   = footPosition [ kCharacterUpAxis ]
        
        # Compute the factors from to avoid values too close to one another.
        currentAnkleFactor = safeDivide( ankleUp - kneeUp , footUp - kneeUp )
        targetAnkleFactor  = ( 1 - tweakParameters.ankleRatio )
        if currentAnkleFactor > targetAnkleFactor:
            # The ankle is farther from the knee that we want.
            ankleFactor = safeDivide( targetAnkleFactor , currentAnkleFactor )
            newAnklePosition = kneePosition + ( anklePosition - kneePosition ) * ( ankleFactor )
        else:
            newAnklePosition = anklePosition
        
        # Compute the toe adjustment either from the old or new ankle position.
        if tweakParameters.useCorrectedAnkleForToe:
            toeAnklePosition = newAnklePosition
        else:
            toeAnklePosition = anklePosition
        
        footFactor = tweakParameters.toeRatio
        newFootPosition = footPosition * ( 1 - footFactor ) + toeAnklePosition * ( footFactor )
    else:
        # Nothing to do.
        newAnklePosition = anklePosition
        newFootPosition  = footPosition
        pass
    
    footJoints[ 'Leg'     ] = kneePosition
    footJoints[ 'Foot'    ] = newAnklePosition
    footJoints[ 'ToeBase' ] = newFootPosition
    
    return footJoints

def convertArms( tweakParameters , elbowPosition , wristPosition ):
    """
    This method takes the position of the hand guides coming out of the
    embedding algorithm (elbow and hand) and maps them to hand joints that
    fits what HumanIK expects.
    """
    
    handJoints = {}
    
    if tweakParameters.tweak:
        handFactor = tweakParameters.ratio
        newWristPosition = wristPosition * ( 1 - handFactor ) + elbowPosition * ( handFactor )
    else:
        # Nothing to do.
        newWristPosition = wristPosition
    
    handJoints[ 'ForeArm' ] = elbowPosition
    handJoints[ 'Wrist'    ] = newWristPosition
    
    return handJoints

def qrGetGuidesFromEmbedding( skeletonParameters , tweakParameters , embedding, bs ):
    """
    This method takes the embedding returned by the skeletonEmbed command and
    converts it to the skeleton guides.
    
    It can add spine, neck and shoulder (clavicle) joints if requested.
    """
    skeletonJoints = {}
    # Add a joint for reference.
    minCorner =  Vector(embedding[ 'boundingBox' ][ 'min' ]) 
    maxCorner = Vector(embedding[ 'boundingBox' ][ 'max' ])
    referenceJoints = convertReference( minCorner , maxCorner )
    skeletonJoints.update( referenceJoints )
    
    # Convert the spine.
    spineCount = skeletonParameters[ 'SpineCount' ]
    wantHipsTranslation = skeletonParameters[ 'WantHipsTranslation' ]
    hipsPosition = Vector( embedding[ 'joints' ][ 'hips' ] )
    backPosition = Vector( embedding[ 'joints' ][ 'back' ] )
    shouldersPosition = Vector( embedding[ 'joints' ][ 'shoulders' ] )
    spineJoints = {} if not bs.input['spine']['execute'] else convertSpine( tweakParameters.spine , spineCount , wantHipsTranslation , hipsPosition , backPosition , shouldersPosition, bs )
    skeletonJoints.update( spineJoints )
    
    # Convert the neck.
    neckCount = skeletonParameters[ 'NeckCount' ]
    headPosition = Vector( embedding[ 'joints' ][ 'head' ] )
    neckJoints = {} if not bs.input['neck']['execute'] else convertNeck( tweakParameters.neck , neckCount , shouldersPosition , headPosition , ( minCorner , maxCorner ) )
    skeletonJoints.update( neckJoints )
    
    # Convert the shoulders.
    shoulderCount = skeletonParameters[ 'ShoulderCount' ]
    leftShoulderPosition  = Vector( embedding[ 'joints' ][ 'left_shoulder' ] )
    rightShoulderPosition = Vector( embedding[ 'joints' ][ 'right_shoulder' ] )
    shoulderJoints = convertShoulder( tweakParameters.shoulder , shoulderCount , shouldersPosition , leftShoulderPosition , rightShoulderPosition, bs )
    skeletonJoints.update( shoulderJoints )
    
    sides = ['left', "right"]

    # Convert the legs.
    for side in sides:
        # Copy the side hips directly.
        targetSide = side.capitalize( )
        
        if(bs.input['legs']['execute']):
            skeletonJoints[ targetSide + 'UpLeg'  ] = Vector( embedding[ 'joints' ][ side + '_thigh'  ] )
        
        kneePosition  = Vector( embedding[ 'joints' ][ side + '_knee'  ] )
        anklePosition = Vector( embedding[ 'joints' ][ side + '_ankle' ] )
        footPosition  = Vector( embedding[ 'joints' ][ side + '_foot'  ] )
        footJoints ={} if not bs.input['legs']['execute'] else  convertFoot( tweakParameters.foot , kneePosition , anklePosition , footPosition )
        skeletonJoints.update( { targetSide + name : position for name , position in footJoints.iteritems( ) } )
    
    # Convert the arms.
    for side in sides:
        elbowPosition = Vector( embedding[ 'joints' ][ side + '_elbow' ] )
        wristPosition  = Vector( embedding[ 'joints' ][ side + '_hand'  ] )
        armJoints = {} if not bs.input['arms']['execute'] else  convertArms( tweakParameters.hand , elbowPosition , wristPosition )
        targetSide = side.capitalize( )
        skeletonJoints.update( { targetSide + name : position for name , position in armJoints.iteritems( ) } )

        
        # Construct hands if necesary
        if (bs.input['hands']['execute']):
            handJoints = convertHands(skeletonJoints, side, bs)
            # targetSide = side.capitalize( )
            # skeletonJoints.update( { targetSide + name : position for name , position in handJoints.iteritems( ) } )

    
   # Copy everything and add the guides.
    guides = { name : [ position.x , position.y , position.z ] for name , position in skeletonJoints.iteritems( ) }
    skeletonGuides = embedding.copy( )
    skeletonGuides[ 'guides' ] = guides
    
    return skeletonGuides

def convertHands(skeletonJoints, side, bs):
    '''Creates the finger joints if required'''
    # offset done by convertHand function duplicated here
    return
    if tweakParameters.tweak:
        handFactor = tweakParameters.ratio
        newWristPosition = wristPosition * ( 1 - handFactor ) + elbowPosition * ( handFactor )
    else:
        # Nothing to do.
        newWristPosition = wristPosition

    handJoints = {}

    # find furthest extent of fingers
    print(bound)
    indexTip = Vector(bound.x, newWristPosition.y, newWristPosition.z)
    # width of the palm
    bs.makeNested(pmc.joint(n = bs.ng("tip", side, "KnucleB"), p = bound))
    width =Vector(newWristPosition-Vector(bs.midpoint(indexTip, newWristPosition))).length()
    lengthMult = -1 if side == "left" else 1

    # create finger chain
    for name in zip(['Pinky','Ring', 'Middle', 'Index', 'Thumb' ], [-.5, -.25, 0, .25, .5]):

        # make joints in the finger
        offsetVector = Vector(abs(name[1]) * lengthMult * (width/2), abs(name[1]) * lengthMult * (width/4), name[1] * width)

        kD = indexTip + offsetVector
        kA = Vector(bs.midpoint(indexTip, newWristPosition)) + offsetVector
        kB = Vector(bs.midpoint(kD, kA))

        kC = Vector(bs.midpoint(kD, kB))

        pmc.select(cl=1)

        handJoints[ bs.ng(name[0], side, "KnucleA")] = bs.makeNested(pmc.joint(n = bs.ng(name[0], side, "KnucleA"), p = kA))
        handJoints[ bs.ng(name[0], side, "KnucleB")] = pmc.joint(n = bs.ng(name[0], side, "KnucleB"), p = kB)
        handJoints[ bs.ng(name[0], side, "KnucleC")] =pmc.joint(n = bs.ng(name[0], side, "KnucleC"), p = kC)
        handJoints[ bs.ng(name[0], side, "KnucleD")] = pmc.joint(n = bs.ng(name[0], side, "KnucleD"), p = kD)

        # slight rotation to show finger orientation
        pmc.rotate(pmc.select(bs.ng(name[0], side, "Knucle*")), [0, 0, -10])

        coords = []
        # generating normal plane
        jts = pmc.ls(bs.ng(name[0], side, "Knucle*"))
        for index, jt in enumerate(jts):
            # lock rotation
            if(index == 0):
                continue
            bs.attrCleanup(jt, ['r', 'tz'] )
            coords.append(pmc.xform(jt, q=1, t=1, ws=1))

        # plane = pmc.polyCreateFacet(
        #     ch=1, p=coords, n="temp_ikPlane01")



        # handJoints[name[0] + "KnucleD"] = indexTip + offsetVector

        # handJoints[name[0] + "KnuckleA"] = Vector(bs.midpoint(indexTip, newWristPosition)) + offsetVector
        # handJoints[name[0] + "KnuckleB"] = Vector(bs.midpoint(indexTip + offsetVector, handJoints[name[0] + "KnuckleA"])) 
        # if(name[0] == "Thumb"):
        #     continue
        # handJoints[name[0] + "KnuckleC"] = Vector(bs.midpoint(indexTip + offsetVector, handJoints[name[0] + "KnuckleB"]))
 
    return handJoints
    

def GenerateGuides(skinShape, **kwargs):
    bs = kwargs['bs']
    # Calcualte skeleton Embed
    result = pmc.skeletonEmbed(skinShape, sm=2, sr= 64)
    #Extract data
    embedding = json.loads( result )
    # Parse data
    extendedEmbedding = qrGetGuidesFromEmbedding( skeletonParameters , tweakParameters , embedding, bs )
    rootTransform = qrCreateGuidesNode( extendedEmbedding)

    guidesNode = pmc.rename( rootTransform , "HumanRig_Guides" )
    pmc.parent(rootTransform, bs.cleanup)

    # Select the output.
    pmc.select( guidesNode , replace=True )