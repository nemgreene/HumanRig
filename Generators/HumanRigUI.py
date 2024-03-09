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

import Dictionary
reload(Dictionary)





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


        self.inputs ={}
        
        # start of head/top of head
        self.inputs['head'] = {}
        self.inputs['head']['execute'] = False
        
        #What is hips translator? 
        self.inputs['hips'] = {}
        self.inputs['hips']['execute'] = False

        # Include toes
        self.inputs['feet'] = {}
        self.inputs['feet']['execute'] = False

        # Include fingers, IK/FK, stretchy
        self.inputs['hands'] = {}
        self.inputs['hands']['execute'] = True
        self.inputs['hands']['variations'] = ["Standard", "Custom"]

        # simple/advanced/variations
        self.inputs['shoulders'] = {}
        self.inputs['shoulders']['execute'] = False
        self.inputs['shoulders']['variations'] = ["Basic", "Advanced"]

        # count, ik/fk?
        self.inputs['neck'] = {}
        self.inputs['neck']['execute'] = False

        # count/variations/stretchy
        self.inputs['spine'] = {}
        self.inputs['spine']['joints'] = 3
        self.inputs['spine']['execute'] = False
        self.inputs['spine']['variations'] = ["Basic", "Advanced"]

        # doubleKnee, flexiplane count, variation
        self.inputs['legs'] = {}
        self.inputs['legs']['execute'] = False
        self.inputs['legs']['variations'] = ["Basic", "Advanced"]

        # doubleElbow, flexiplane count, variation
        self.inputs['arms'] = {}
        self.inputs['arms']['execute'] = True
        self.inputs['arms']['joints'] = 3
        self.inputs['arms']['variations'] = ["Basic", "Advanced"]

        self.bs = bs



    def __reload(self) :
        
        # check if checkbox is enabled per section of the rig

        # spineActive = pmc.checkBox( self.spineToggle , query=True, v=1 )
        # pmc.frameLayout(self.spineSettings, edit = 1, visible = spineActive)
        for i in zip(self.executeToggles, self.settingFrames):
            active = pmc.checkBox( i[0] , query=True, v=1 )
            pmc.frameLayout(i[1], edit = 1, visible = active)
            
        # cmds.layout( self.spineSettings , edit=True , visible=spineActive )
        
    def toggleActive(self):
        self.__reload()


    
    def create( self, baseScripter ):
        # Destroy current window if it already exists.

        #    Create a new template.
        #
        if pmc.window( self.windowName, exists=True ):
                pmc.deleteUI( self.windowName, uiTemplate=True, window=True )

        template = uiTemplate(self.windowName, force=True)
        template.define(frameLayout, borderVisible=False, labelVisible=False)
        template.define(columnLayout, adj=1)


        window =pmc.window(self.windowName, title = self.windowName, menuBar=True,menuBarVisible=True)
        setUITemplate( self.windowName, pushTemplate=True )
        self.executeToggles, self.settingFrames, self.variationMenus = [], [], []

        
        with window:

            # Enable/Disable sections of rig, setting rig parameters
            with columnLayout():
                    with frameLayout(mw=15, mh = 10):
                        # ShouldersSettings
                        self.executeToggles.append(pmc.checkBox(label = "Shoulders", cc = lambda x: self.toggleActive()))
                        self.shouldersSettings = frameLayout(label="Shoulders Frame")
                        self.settingFrames.append(self.shouldersSettings)
                        shouldersVariant = optionMenu()
                        self.variationMenus.append(shouldersVariant) 
                        with LayoutManager(self.shouldersSettings):
                            with columnLayout():
                                with shouldersVariant:
                                    map(lambda x : menuItem(label = x),self.inputs['shoulders']['variations'] )

                        # ArmSettings
                    with frameLayout(mw=15, mh = 10):
                        self.executeToggles.append(pmc.checkBox(label = "Arms", cc = lambda x: self.toggleActive(), v = self.inputs['arms']['execute']))
                        self.armsSettings = frameLayout(label="arms Frame")
                        self.settingFrames.append(self.armsSettings)
                        armVariant = optionMenu()
                        self.variationMenus.append(armVariant) 
                        with LayoutManager(self.armsSettings):
                            with columnLayout():
                                with armVariant:
                                    map(lambda x : menuItem(label = x),self.inputs['arms']['variations'] )

                        # handSettings
                    with frameLayout(mw=15, mh = 10):
                        self.executeToggles.append(pmc.checkBox(label = "Hands", cc = lambda x: self.toggleActive(), v = self.inputs['hands']['execute']))
                        self.handsSettings = frameLayout(label="hands Frame")
                        self.settingFrames.append(self.handsSettings)
                        handsVariant = optionMenu()
                        self.variationMenus.append(handsVariant) 
                        with LayoutManager(self.handsSettings):
                            with columnLayout():
                                with handsVariant:
                                    map(lambda x : menuItem(label = x),self.inputs['hands']['variations'] )

                    #     # Leg Settings
                    # with frameLayout(mw=15, mh = 10):
                    #     self.executeToggles.append(pmc.checkBox(label = "Legs", cc = lambda x: self.toggleActive()))
                    #     self.legsSettings = frameLayout(label="legs Frame")
                    #     self.settingFrames.append(self.legsSettings)
                    #     with LayoutManager(self.legsSettings):
                    #         with columnLayout():
                    #             with optionMenu():
                    #                 map(lambda x : menuItem(label = x),self.inputs['legs']['variations'] )
                    
                    with frameLayout():
                        with columnLayout():
                            button(label = "Generate Guides",  c =lambda x :self.generateButton() )


                    # with frame:
                    #     with optionMenu():
                    #         menuItem(label='Red')
                    #         menuItem(label='Green')
                    #         menuItem(label='Blue')

        setUITemplate( popTemplate=True )
        pmc.showWindow( window )
        self.__reload()
        return self
    
    def generateButton(self):
        # Bind inputs selected by user to self.input map
        # Bind by element label to input map if bones are necessary 

        for index, toggleElem in enumerate(self.executeToggles):
            # query if execution is selected
            active = pmc.checkBox(toggleElem, query = 1, value=1) 
            self.inputs[pmc.checkBox(toggleElem, query = 1, label = 1).lower()]["execute"] = active
            if(active):
                # query variation selected
                self.inputs[pmc.checkBox(toggleElem, query = 1, label = 1).lower()]["variation"] = pmc.optionMenu(self.variationMenus[index], query = 1, value=1) 
            
            

        self.bs.boundGenerateGuides(self.inputs)

    
    # def updateUI( self ):
    #     """
    #     This method performs a full UI refresh.
        
    #     It refreshes the character list and its associated buttons.  It also
    #     refreshes the HumanIK tool.
    #     """
        
    #     # Apparently, updating the modes first reduces flickering when switching
    #     # from None character to an actual character and vice-versa.
    #     self._updateCharacterList( )
    #     self._updateCharacterButtons( )
    #     self._updateModes( )
    #     qruiRefreshMeshes( self )
    #     qruiRefreshGuidesColor( self )
        
    #     hikUpdateTool( )
    
    
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

class BoundObject(object):
    '''Alpha version of a Reactjs style binding of UI elements to values that automatically re-render the element on value change
    '''
    def __init__(self, pymelUIElement, **kwargs):
        # element must be executed at runtime, deferred to elemGetter
        self._elem = pymelUIElement
        # ref to self element to update it on valueSetter
        self._ref = None
        # stored kwargs
        self._kwargs = kwargs
        # when this value is updated, the UI element is rerendered
        self._value = None
       

    @property
    def elem(self):
        # Getter of element
        # execute UI generation, and stor reference for updating
        self._ref = self._elem(**self._kwargs)
        return self._ref

    @elem.setter
    def elem(self):
        # Elem Setter
        return self._ref

    @elem.deleter
    def elem(self):
        del self._elem

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, updatedValue):
        # On call of statChanger, the UI elements wil be rerendered

        # if kwarg v is lambda, execute callback and inject kwargs to be mutated
        if(callable(updatedValue['v']) and updatedValue['v'].__name__ == "<lambda>"):
            try:
                # Kwargs chould have been updated by the lambda
                temp = self._kwargs.copy()
                temp.update({"e": 1})
                # Refresh the UI
                return self._elem(self._ref, **temp)
            except:
                print("Key not found")
            pass
        else:
            # Get kwargs
            temp = self._kwargs.copy()
            # get updated keys
            temp.update(**updatedValue)
            # rerender the UI
            temp.update({"e": 1})

            return self._elem(self._ref, **temp)


def ReactComponent(elem, **staticValues):
    '''Reactify function that generates the class, and exposees the element and the setValue function bound to it
    
    Example:
    //Create a checkbox and inject kwargs
    [elem, setValue] = ReactComponent(pmc.checkBox, label = "TestL Label", v=1) 
    
    with window:
        with pmc.columnLayout():
            with pmc.frameLayout():
                
                //render window in hierarchy
                elem()
                
                //Explicitly change its value
                setValue(v= lambda x : x.update({'v': 0}) )

                with pmc.columnLayout():
                        pmc.button(label = "Toggle", 
                        
                        //setValue can also be passed a lambda that updates the kwargs dict, injected into x
                        c=lambda x : setValue(v = lambda x : x.update({'v': not x['v']})))

    '''
    c = BoundObject(elem, **staticValues)
    return lambda : c.elem, lambda **staticValues : c.__setattr__("value", staticValues)

[elem, setValue] = ReactComponent(pmc.checkBox, label = "TestL Label", v=1) 

