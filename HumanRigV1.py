import sys
import os
import pymel.core as pmc


bs =  r'G:\My Drive\Maya\MyScripts\BaseScripter'
generators =  r'G:\My Drive\Maya\MyScripts\HumanRig\Generators'

for p in [bs, generators]:
    if p not in sys.path:
        sys.path.append(p)


import baseScripter
import Dictionary
import HumanRigUI
import CreateGuides

reload(CreateGuides)
reload(baseScripter)
reload(Dictionary)
reload(HumanRigUI)


'''
Character should be Z+ facing
'''

bs= baseScripter.BaseScripter(name = "HumanRig")
ui = HumanRigUI.QuickRigTool(bs)

# initialize generates all joints
# bind joints to subObjects
# joints not requested by ui should be dumped

# Functions steps will be centralized here, then distributed to the UI to be called as necessary

def boundGenerateGuides(self, input):
        
        # Function called from the UI class that embeds the skeleton, then removes unwanted joints 

        children = (pmc.listRelatives(bs.cleanup, c=1))
        proc = True
        if(len(children) != 0):
            proc = bs.requestConfirmation("Warning", "Delete Rig and reinitialize guides? All progress will be lost")

        if(not proc):
            return
        print("Embedding Skeleton")
        pmc.delete(children)


        bs.input = input
        bs.guides = CreateGuides.GenerateGuides(pmc.listRelatives(pmc.ls("mesh_link1")[0], shapes=True)[0], bs=bs) 

        
        # after guides are generated, reference Input and see which are needed

bs.boundGenerateGuides = boundGenerateGuides.__get__(bs)
# -----------------------------------------EntryPoint-------------------------

def initialize():
    uiObj = ui.create(bs)

# execute the initialization of the UI
bs.execute(initialize)

