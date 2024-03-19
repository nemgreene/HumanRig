import Dictionary
import HandGenerator
import ShouldersGenerator
import ArmGenerator

reload(Dictionary)
reload(HandGenerator)
reload(ShouldersGenerator)
reload(ArmGenerator)


Nexus = {}
d = Dictionary

# Hand Generator
Nexus[d.chain_hands] = {}
Nexus[d.chain_hands][d.guides_custom] = HandGenerator.convertHands
Nexus[d.chain_hands][d.mirror_hands] = HandGenerator.mirrorHands
Nexus[d.chain_hands]['variations'] = HandGenerator.executionThreads

# Shoulder
Nexus[d.chain_shoulders] = {}
Nexus[d.chain_shoulders][d.guides_secondary] = ShouldersGenerator.generateSecondaryGuides
Nexus[d.chain_shoulders][d.generate_rig] = ShouldersGenerator.generateRig
Nexus[d.chain_shoulders]['variations'] = ShouldersGenerator.executionThreads

# Arms
Nexus[d.chain_arms] = {}    

Nexus[d.chain_arms][d.generate_frame] = ArmGenerator.generateFrame
Nexus[d.chain_arms][d.guides_secondary] = ArmGenerator.generateSecondaryGuides
Nexus[d.chain_arms][d.generate_rig] = ArmGenerator.generateRig
Nexus[d.chain_arms]['variations'] = ArmGenerator.executionThreads

# Linking chains to reguired guides
Nexus[d.requiredTable] = {}
Nexus[d.requiredTable][d.chain_shoulders] = [d.chain_neck, d.chain_hips]



def chainRequired(queriedChain, input):
    '''Checks required table to see if any'''
    # get list of all required execution chains
    exeuctionChains = [x for x in input if ("execute" in input[x] and input[x]['execute'])]
    directlyRequired = queriedChain in exeuctionChains

    # next, chek requirements table
    requiredByExecution = [Nexus[d.requiredTable][x] for x in exeuctionChains if x in Nexus[d.requiredTable]]
    # flatten 1 level down
    requiredByExecution = [item for items in requiredByExecution for item in items]
    secondaryRequired = queriedChain in requiredByExecution

    return directlyRequired or secondaryRequired

Nexus[d.chainRequired] = chainRequired