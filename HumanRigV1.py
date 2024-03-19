import sys
import os
import pymel.core as pmc


bs =  r'G:\My Drive\Maya\MyScripts\BaseScripter'
scripts =  r'G:\My Drive\Maya\MyScripts\HumanRig\scripts'
generators =  r'G:\My Drive\Maya\MyScripts\HumanRig\scripts/Generators'
subscripts =  r'G:\My Drive\Maya\MyScripts\HumanRig\scripts/Generators/SubScripts'

for p in [bs, generators, scripts, subscripts]:
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
And stood on top of world origin
'''
pmc.select(cl=1)
bs= baseScripter.BaseScripter(name = "HumanRig")
ui = HumanRigUI.QuickRigTool(bs)
d = Dictionary
d.bs = bs

bs.makeNesting([{"Temp" : ["ShoulderTemp"], }, d.g_globalStatic, d.g_globalDynamic] )
# initialize generates all joints
# bind joints to subObjects
# joints not requested by ui should be dumped

# Functions steps will be centralized here, then distributed to the UI to be called as necessary

def boundGenerateGuides(self, input):
        
        # Function called from the UI class that embeds the skeleton, then removes unwanted joints 
        children = (pmc.listRelatives(bs.cleanup, c=1))
        proc = True
        # if(len(children) != 0):
        #     proc = bs.requestConfirmation("Warning", "Delete Rig and reinitialize guides? All progress will be lost")

        if(not proc):
            return

        bs.input = input
        bs.update = CreateGuides.GenerateGuides(pmc.listRelatives(pmc.ls("Skin2")[0], shapes=True)[0], bs=bs) 
        return bs
        
        # after guides are generated, reference Input and see which are needed

bs.boundGenerateGuides = boundGenerateGuides.__get__(bs)
# -----------------------------------------EntryPoint-------------------------

def initialize():
    # All ccs may be added here
    bs.ccs ={}
    # Potential wolution for all the loose threads
    bs.temps = {}
    uiObj = ui.create()
    uiObj.generateAutoRig()

# execute the initialization of the UI

print("-----------------------------------------------------------------------")
print("-----------------------------------------------------------------------")
print("-----------------------------------------------------------------------")
print("-----------------------------------------------------------------------")
bs.execute(initialize)
