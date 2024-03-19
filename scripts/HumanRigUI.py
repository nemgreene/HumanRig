import pymel.core as pmc
from pymel.core import *

import maya
# maya.utils.loadStringResourcesForModule(__name__)


import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMaya as OpenMaya
from maya.common.ui import LayoutManager
from maya.common.ui import showMessageBox
from maya.common.ui import showConfirmationDialog
from maya.common.utils import getSourceNodes
from maya.common.utils import getSourceNodeFromPlug
from maya.common.utils import getSourceNode
from maya.common.utils import getIndexAfterLastValidElement
import json
from math import degrees , fabs , sqrt
from functools import partial , wraps
import re
from pymel.core.datatypes import Vector

import Dictionary
reload(Dictionary)

import NexusGenerator
reload(NexusGenerator)



d = Dictionary

kFrameMarginWidth = 25
kFrameMarginHeight = 4
kFrameParam = dict( marginWidth=kFrameMarginWidth , marginHeight=kFrameMarginHeight , collapse=False , collapsable=True )
kRowLayoutHeight = 21
kSkeletonFieldWidth = 60
kOptionsTextWidth = 90
kOptionsButtonWidth = 40
kColorSwatchWidth = 30
kColorSwatchHeight = 30
kColorSwatchColorWidth = 15
kColorSwatchColorHeight = 15



class QuickRigTool:
    """
    This is the main UI class for the QuickRig tool.
    
    It handles creation of the UI and provides various callbacks to handle
    user interactions.
    """
    
    def __init__( self ,bs,windowName="quickRigWindowId" ):
        """
        Simple constructor.
        
        It does not create the UI.  UI creation is deferred until create() is
        called
        """
        
        self.windowTitle = maya.stringTable['y_quickRigUI.kQuickRigWindowName' ]
        self.windowName  = windowName
        
        # This is the default error handler.  It can be overwritten if, for instance
        # some scripting tool wants to be notified in a different way.
        self.handleError = QuickRigTool.__handleError
        # Same idea for confirmation requests.
        self.requestConfirmation = QuickRigTool.__requestConfirmation

        self.bs = bs
        self.bs.nexus = NexusGenerator.Nexus

        self.bs.input = {}
        self.bs.input['frames']={}
        self.bs.input['elements'] = {}
        # extract all execution threads and variations
        for chain in d.chains:
            self.bs.input[chain] = {}
            self.bs.input[chain]['execute'] = False
            if(chain not in self.bs.nexus): continue
            if("variations" in self.bs.nexus[chain]):
                self.bs.input[chain]['variations'] = self.bs.nexus[chain]['variations']

        self.bs.input[d.chain_arms]['execute'] = True

    def __reload(self) :
        '''reloads all frames visibility'''
        # check if checkbox is enabled per section of the rig
        for i in zip(self.executeToggles, self.settingFrames):
            active = pmc.checkBox( i[0] , query=True, v=1 )
            pmc.frameLayout(i[1], edit = 1, visible = active)


    def toggleActive(self):
        self.__reload()

    def selectVariation(self, item, chain):
        self.bs.input[chain]['variation'] = item
        print()
        for chain in d.chains:
            # any time an option changes, the UI may need to update the individual frameGenerators coming from each generator
            try:
                self.bs.nexus[chain][d.generate_frame](self.bs.input, refresh = 1)
            except: 
                pass
        # self.__reload()

    def generateSettingsFrame(self, dic):
        ret = pmc.frameLayout(**self.settingsFrames)
        with ret:
            self.executeToggles.append(pmc.checkBox(label = dic.capitalize(), cc = lambda x: self.toggleActive(), v = self.bs.input[dic]['execute']))
            self.temp = frameLayout(label=dic + "Frame")
            self.settingFrames.append(self.temp)
            if("variations" in self.bs.input[dic] and len(self.bs.input[dic]['variations']) > 1 ):
                hipsVariant = optionMenu( acc=1,cc= lambda x : self.selectVariation(x, dic))
                self.variationMenus.append(hipsVariant) 
                with LayoutManager(self.temp):
                    with columnLayout():
                        with hipsVariant:
                            map(lambda x : menuItem(label = x,),self.bs.input[dic]['variations'] )
            try:
                with pmc.frameLayout(**self.settingsFrames):
                    self.bs.nexus[dic][d.generate_frame](self.bs.input)
            except:
                pass
        return ret
    
    
    def create( self ):
        if pmc.window( self.windowName, exists=True ):
                pmc.deleteUI( self.windowName, uiTemplate=True, window=True )

        template = uiTemplate(self.windowName, force=True)
        template.define(frameLayout, borderVisible=False, labelVisible=False)
        template.define(columnLayout, adj=1)


        window =pmc.window(self.windowName, title = self.windowName, menuBar=True,menuBarVisible=True)
        setUITemplate( self.windowName, pushTemplate=True )
        self.executeToggles, self.settingFrames, self.variationMenus = [], [], []

        
        with window:
            with LayoutManager( cmds.scrollLayout( childResizable=True ) ):
                with LayoutManager( cmds.columnLayout( adjustableColumn=True ) ):
                    with columnLayout(adjustableColumn=True):
                        # Enable/Disable sections of rig, setting rig parameters
                            # Generate all the frames for the setting
                            self.settingsFrames = {'mw' : 10, "mh" : 2}
                            for frame in d.chains:
                                self.generateSettingsFrame(frame)
                            
                            with frameLayout(**self.settingsFrames):
                                with columnLayout():
                                    button(label = d.uil_generateBaseGuides,  c =lambda x :self.generateBasicGuides() )

                            with frameLayout(**self.settingsFrames):
                                with columnLayout():
                                    with rowLayout(nc = 2, nch=2 ):
                                        button(label = d.uil_mirrorLtR, c = Callback(lambda : self.mirrorGuides(True)))
                                        button(label = d.uil_mirrorRtL, c = Callback(lambda : self.mirrorGuides(False)))

                            with frameLayout(**self.settingsFrames):
                                with columnLayout():
                                    button(label = d.uil_generateSecondaryGuides,  c =lambda x :self.generateSecondaryGuides() )
                            with frameLayout(**self.settingsFrames):
                                with columnLayout():
                                    button(label = d.uil_createRig,  c =lambda x :self.generateRig() )
                            with frameLayout(**self.settingsFrames):
                                with columnLayout():
                                    button(label = "AutoRig",  c =lambda x :self.generateAutoRig() )

        setUITemplate( popTemplate=True )
        pmc.showWindow( window )
        self.__reload()
        return self


    def generateBasicGuides(self):
        '''Generates the guides based off the chains requested by the user'''
        # Bind input selected by user to self.bs.input map
        # Bind by element label to input map if bones are necessary 
        
        # collect input
        for toggleElem in self.executeToggles:
            # query if execution is selected
            active = pmc.checkBox(toggleElem, query = 1, value=1) 
            label = pmc.checkBox(toggleElem, query = 1, label = 1).lower()
            self.bs.input[label]["execute"] = active

        for option in self.variationMenus:
            self.bs.input[label]["variation"] = pmc.optionMenu(option, query = 1, value=1) 

        self.bs = self.bs.boundGenerateGuides(self.bs.input)
            # unify joint radius
        [pmc.joint(x, e=1, rad = self.bs.joint_radius) for x in self.bs.joints]

    def mirrorGuides(self, leftToRight = True):
        '''Function to mirror joints either l->r or r->l'''

        src = d.s_Left if leftToRight else d.s_Right
        targ = d.s_Left if not leftToRight else d.s_Right
        guides = {}
        # verify guides have been generatesd
        try:
            guides = self.bs.guides
            assert guides
        except:
            self.__handleError("Generate guides first")
            return
        
        filteredGuides = filter(lambda x : "Knuckle" not in x, guides)
        for guide in filteredGuides:
            # if Origin side, do nothing
            if(src in guide):
                # make sure that any udpates to the joints are in the dictionary
                self.bs.guides[guide] = pmc.xform(self.bs.joints[guide], q=1, ws=1, t=1)
                continue
            # Mirror joints and guides on the opposite side
            if(targ in guide):
                # update guide first
                srcName = re.sub(targ, src, guide)
                # Delete original joint
                sourceJointPosition = pmc.xform( srcName , query=True , worldSpace=True , translation=True )
                # Mirror the joint position.
                destJointPosition = sourceJointPosition
                destJointPosition[ 0 ] = 0 - ( destJointPosition[ 0 ] - 0 )
                self.bs.guides[guide] = destJointPosition
                pmc.xform( guide , worldSpace=True , translation=destJointPosition )
                continue
            # guides must be at centerline
            if(d.p_snapToCenterOnMirror):
                destJointPosition =  Vector(pmc.xform( guide , query=True , worldSpace=True , translation=True ))
                destJointPosition.x = 0
                self.bs.guides[guide] = destJointPosition
                pmc.xform( guide , worldSpace=True , translation=destJointPosition )
            else:
                destJointPosition =  Vector(pmc.xform( guide , query=True , worldSpace=True , translation=True ))
                hipsPosition = Vector(pmc.xform( self.bs.joints[d.j_hipName] , query=True , worldSpace=True , translation=True ))
                destJointPosition.x = hipsPosition.x
                self.bs.guides[guide] = destJointPosition
                pmc.xform( guide , worldSpace=True , translation=destJointPosition )

        # custom mirror function called every click 
        # Some custom mirror functions may be needed, call here
        if(self.bs.nexus[d.chainRequired](d.chain_hands, self.bs.input)):
            self.bs.nexus[d.chain_hands][d.mirror_hands](self, leftToRight, src, targ)
                
    def generateSecondaryGuides(self):
        for chain in d.chains:
            if not(self.bs.nexus[d.chainRequired](chain, self.bs.input)):
                continue
            try:
                if (d.guides_secondary not in self.bs.nexus[chain]):
                    continue
                if(d.guides_secondary in self.bs.nexus[chain]):
                    self.bs.nexus[chain][d.guides_secondary](self.bs)
            except Exception as error:
                print("Error in secondary guides", chain, error)
                continue

        # unify joint radius
        [pmc.joint(x, e=1, rad = self.bs.joint_radius) for x in self.bs.joints]
        

    def generateRig(self):
        for chain in d.chains:
            if not(self.bs.nexus[d.chainRequired](chain, self.bs.input)):
                continue
            try:
                if (d.generate_rig not in self.bs.nexus[chain]):
                    continue
                if(d.generate_rig in self.bs.nexus[chain]):
                    self.bs.nexus[chain][d.generate_rig](self.bs)
                    pmc.select(cl=1)
            except Exception as error:
                print("Error in generating rig", chain, error)
                continue
    
    def generateAutoRig(self):
        self.generateBasicGuides()
        self.mirrorGuides(True)
        self.generateSecondaryGuides()
        self.generateRig()

    @staticmethod
    def __handleError( message ):
        """
        This method is the default error handler for user errors.
        
        It simply shows a dialog box with the error message.
        """
        
        showMessageBox(
            title=maya.stringTable['y_quickRigUI.kErrorTitle' ] ,
            message=message ,
            icon='critical'
            )
    
    
    @staticmethod
    def __requestConfirmation( title , message ):
        """
        This method is the default handler to request confirmation.
        
        It simply shows a ok / cancel dialog box with the message.
        """
        
        return showConfirmationDialog( title , message )
    
    
    @staticmethod
    def __callbackWrapper( *args , **kwargs ):
        """
        This method is a wrapper in the form expected by UI elements.
        
        Its signature allows it to be flexible with regards to what UI elements
        expects.  Then it simply calls the given functor.
        """
        
        kwargs[ 'functor' ]( )
    
    
    def _callbackTool( self , function ):
        """
        This method returns a callback method that can be used by the UI
        elements.
        
        It wraps the "easier to define" callbacks that only takes the tool as
        an element into the callbacks that UI element expects.
        """
        
        functor = partial( function , tool=self )
        return partial( QuickRigTool.__callbackWrapper , functor=functor )

