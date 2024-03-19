import pymel.core as pmc
import maya.api.OpenMaya as om
from pymel.core.datatypes import Vector

import Dictionary
reload(Dictionary)

d = Dictionary
# finger = "index"
# # what is being rigged
# chain = finger
# # pole vector location offset
# pvOffset = [0,0,1 ]
# # general scale multiplier for the rig components

# # joint radius's: [ik, fk, bind]
# radiusArr = [.5 * sm, .3 * sm, .1 * sm]
# # which side are we rigging on
# side = "r"
# # BETA: This rig is defaulted to the lefthand of a rig
# # For a rig with mirrored ccs, turn on true
# mirrored = True
# # name of the overall group
# name = this.bs.ng("grp", side, chain, "rig01")
# # "names of the individual components"
# names = [finger + "A", finger + "B", finger + "C", finger + "D",]
# # names = ["shoulder", "elbow", "wrist"]


# debug = False

# # the driver cc can be overridden at this line
# # this cc needs to NOT have the attr "ArmIKFK"
# try:
#     driverCC = pmc.ls("anim_r_arm_misc01")[0]
#     # debug = False
# except:
#     driverCC = None
#     # debug =


# NEEDS WORK/
    
# Remove from historically interesting
# make sure that if script has already run and driverCC has ik attr, it doesnt err out


class IFKConstructor():
    # Expecting joint orientation with x pointed at child(or away if mirrored), and y pointing up

    def __init__(this, generator_params):
        this.coords = []
        this.orients = []
        this.scales = []
        this.fkCCs = []
        this.ikJts = []
        this.baseJts = []
        
        # {bs, names : [], side, chain, joints, radiusArr, h_ccs, h_misc, h_joint, h_temp}
        this.bs = generator_params.bs
        this.targetJts = generator_params.targetJts
        this.names = generator_params.names
        this.side = generator_params.side
        this.pvOffset = generator_params.pvOffset
        this.chain = generator_params.chain
        this.radiusArr = generator_params.radiusArr
        this.ccs = generator_params.g_ccs
        this.g_joint = generator_params.g_joint
        this.misc = generator_params.g_misc
        this.g_temp = generator_params.g_temp
        try:
            this.driverCC = generator_params.driverCC
        except:
            this.driverCC = None
        this.mirrored = True if this.side == d.s_Right else False

        # will depend side to side
        this.radiusArr = [x * this.bs.joint_radius for x in this.radiusArr]
        # print(bs.joint_radius)
        # bs.makeHierarchy({chain})

    def initChains(this):
        # sanitize and reconstruct the joint chain to avoid flipping issues
        for index, jt in enumerate(this.targetJts):
            this.coords.append(pmc.xform(jt, q=1, t=1, ws=1))
        # generating normal plane
        this.plane = pmc.polyCreateFacet(
            ch=1, p=this.coords, n="temp_ikPlane01")
        pmc.parent(this.plane[0], this.bs.cleanup)
        parent = pmc.spaceLocator(n="parent")
        up = pmc.spaceLocator(n="up")
        targ = pmc.spaceLocator(n="targ")
        world = pmc.spaceLocator(n="world")
        pmc.parent([parent, up, targ, world], this.bs.cleanup)

        
        pmc.delete(pmc.pointConstraint(this.targetJts[0], parent))
        pmc.delete(pmc.parentConstraint(this.targetJts[0], up))
        pmc.delete(pmc.pointConstraint(this.targetJts[0], world))
        pmc.delete(pmc.pointConstraint(this.targetJts[-1], targ))

        pmc.move(up, [0, .5, 0], os=1, r=1)
        pmc.delete(pmc.aimConstraint(targ, parent, aim=[
                   1, 0, 0], wut="object", wuo=up))
        pmc.parent(this.plane[0], parent)
        pmc.move(world, [1, 0, 0], r=1, ws=1)
        pmc.aimConstraint(world, parent, aim=[
            1, 0, 0], wut="scene", u=[0, -1, 0] if this.mirrored else [0, 1, 0])
        pmc.select(cl=1)
        prev = this.bs.cleanup
        for index, cv in enumerate(pmc.ls(this.bs.ag(this.plane[0], "vtx[*]"), fl=1)):
            x, y, z = pmc.xform(cv, q=1, t=1, ws=1)
            jt = pmc.joint(prev,
                            # n = d.jtName(this.names[index], side = this.side)
                           n="jt_base_" + this.side + "_" + this.names[index] + "01"
                           , p=(x, y, z))
            this.baseJts.append(jt)
            pmc.setAttr(str(jt) + ".radius", this.radiusArr[0])
            if (index > 0):
                pmc.parent(jt, w=1)
                pmc.delete(pmc.aimConstraint(jt, prev, aim=[1, 0, 0]))
                pmc.parent(jt, prev)

            prev = jt
        #
        pmc.delete(pmc.orientConstraint(this.baseJts[-2], this.baseJts[-1]))
        pmc.parent(this.plane[0], this.bs.groups["Temp"])
        pmc.delete([parent, up, targ, world])
        pmc.parent(this.baseJts[0], this.g_joint)
        return

    def makeIK(this):
        def makeCCs():
            # make shapes
            this.startCC = pmc.circle(
                r=this.bs.joint_radius, n=this.bs.ng("anim", "IK", this.side, this.chain, "start"))
            # pmc.delete(this.startCC, ch=1)
            pmc.rotate(
                pmc.ls(this.bs.ag(this.startCC[0], "cv[*]")), [90, 0, 0], r=1, os=1, fo=1, )
            this.globalMove = pmc.duplicate(this.startCC[0],
                                            n=this.bs.ng("anim", this.side, this.chain, "globalMove"))
            pmc.scale(
                pmc.ls(this.bs.ag(this.globalMove[0], "cv[*]")), [1.5, 1.5, 1.5], r=1, os=1, )
            this.endCC = pmc.duplicate(
                this.startCC[0], n=this.bs.ng("anim", "IK", this.side, this.chain, "end"))
            this.pvCC = pmc.curve(d=1, p=[[-.75, -0.0, 0.0], [0.0, 0.0, -.75], [.75, -0.0, 0.0], [0.0, -0.0, .75], [-.75, -0.0, 0.0], [0.0, .75, 0.0], [0.0, 0.0, -.75], [0.0, -0.0, .75], [0.0, .75, 0.0], [.75, -0.0, 0.0], [-.75, -0.0, 0.0], [
                0.0, -.75, -0.0], [.75, -0.0, 0.0], [0.0, -0.0, .75], [0.0, -.75, -0.0], [0.0, 0.0, -.75]], k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], n=this.bs.ng("anim", "IK", this.side, this.chain, "pvCtrl", "IK"))

            this.ikJts = pmc.duplicate(this.baseJts)
            for index, jt in enumerate(this.ikJts):
                pmc.rename(jt, d.ikName(this.names[index], side = this.side) )
                pmc.setAttr(str(jt) + ".radius", this.radiusArr[0])

            pmc.delete(pmc.parentConstraint(this.ikJts[0], this.startCC))
            pmc.scale(this.pvCC,[this.bs.joint_radius, this.bs.joint_radius, this.bs.joint_radius])
            pmc.makeIdentity(this.pvCC, a=1, t=1, s=1, r=1)

            pmc.delete(pmc.parentConstraint(this.ikJts[-1], this.endCC))

            pmc.parent(this.startCC[0], this.endCC[0], this.pvCC, this.ccs)
            # control the hierarchy

            # handle pv placement
            temp = pmc.spaceLocator(n="locAlign_temp01")
            pmc.parent(temp, this.bs.cleanup)
            pmc.delete(pmc.pointConstraint(
                this.ikJts[len(this.ikJts)/2], temp))
            pmc.normalConstraint(this.plane, temp, w=1, aim=[0, 1, 0])
            
            startPos = Vector(pmc.xform(this.targetJts[0], q=1, ws=1, t=1))
            endPos = Vector(pmc.xform(this.targetJts[-1], q=1, ws=1, t=1))
            distance = startPos.distanceTo(endPos) * .5


            pmc.move(this.pvOffset[0] * distance, this.pvOffset[1] * distance, this.pvOffset[2] * distance, temp, r=1, os=1)
            # place cc
            pmc.delete(pmc.pointConstraint(temp, this.pvCC))
            pmc.delete(pmc.aimConstraint(
                this.ikJts[1], this.pvCC, aim=[0, 1, 0]))
            pmc.delete(temp)
            pmc.delete(this.plane)
            
            # make little pointer curve
            this.pvCurve = pmc.curve(d=1, n=this.bs.ng("cc", this.side, this.chain, "pvPointer"), p=[
                (0, 0, 0), (1, 1, 1)], k=[0, 1])
            pmc.setAttr(this.bs.ag(this.pvCurve, "template"), 1)
            cvs = pmc.ls(str(this.pvCurve) + ".cv[*]", fl=1)
            for index, cv in enumerate(cvs):
                clus = pmc.cluster(cv, n=this.bs.ng("clus", this.side, this.chain,
                                            "pvPointer", ("A" if index == 0 else "B")))
                pmc.hide(clus)
                pmc.pointConstraint(this.pvCC if index ==
                                    0 else this.ikJts[len(this.ikJts)/2], clus[1])
                grp = pmc.group(clus,  n=this.bs.ng("grpOffset", this.side, this.chain,
                                            "pvPointer", ("A01" if index == 0 else "B01")))
                pmc.parent(grp, this.bs.cleanup)
            pmc.parent(this.pvCurve, this.ccs)
            # reset cc position
            grps = []
            for index, cc in enumerate([this.startCC[0],  this.pvCC, this.endCC[0],]):
                d.setCCColorBySide(cc, this.side)
                grp = pmc.group(em=1, n=this.bs.ng(
                    "grpOffset", this.side, this.names[index]))
                grps.append(grp)
                pmc.delete(pmc.parentConstraint(cc, grp))
                pmc.parent(cc, grp)
                pmc.parent(grp, this.misc)

            if(this.mirrored):
                pmc.scale(grps[0], [1,1,-1])
                pmc.scale(grps[1], [1,1,-1])
                pmc.scale(grps[2], [1,1,-1])

            pmc.parent([grps[1], grps[2]], this.startCC[0])
            # pmc.parentConstraint(this.startCC, this.ikJts[0], mo=1)
            # IKHandles
            for jt in this.ikJts:
                pmc.joint(jt, e=1, spa=1, ch=1,)

            ik = pmc.ikHandle(
                sj=this.ikJts[0], ee=this.ikJts[-1], n=this.bs.ng("ik", this.side, this.chain, "handle01"))
            
            pmc.poleVectorConstraint(this.pvCC, ik[0])
            pmc.pointConstraint(this.endCC, ik[0], mo=1)
            pmc.parent(ik[0], this.misc)
            pmc.hide(ik[0])
            pmc.parent(pmc.group(this.ikJts[0], n=d.ng(
            "grp",this.chain, "IK")), this.g_joint)

            this.endCC[0].addAttr("Stretchy", defaultValue=1.0,
                                  minValue=0, maxValue=1, h=0, k=1, r=1, w=1)
            this.endCC[0].addAttr("Nudge", defaultValue=0,
                                  h=0, k=1, r=1, w=1)
            this.endCC[0].addAttr("NudgeMultiplier", defaultValue=.01,
                                  h=0, k=1, r=1, w=1)
            temp = pmc.orientConstraint(this.endCC[0], this.ikJts[-1], mo=1)
            if(this.mirrored):
                pmc.setAttr(this.bs.ag(temp, "offsetZ"), 180)
            # this.endCC[0].addAttr("Lock", defaultValue=0,
            #                       minValue=0, maxValue=1, h=0, k=1, r=1, w=1)

            pmc.pointConstraint(this.startCC, this.ikJts[0])
            # handle global move/scale
            pmc.delete(pmc.parentConstraint(this.startCC, this.globalMove))
            this.globalMoveGrp = pmc.group(
                em=1, n=this.bs.ng("grpOffset", this.side, this.chain, "globalMove01"))
            pmc.parent(this.globalMoveGrp, this.ccs)
            pmc.delete(pmc.parentConstraint(
                this.globalMove, this.globalMoveGrp))
            pmc.parent(this.globalMove[0], this.globalMoveGrp)
            pmc.rename(str(pmc.listRelatives(
                this.ikJts[-2], children=1)[-1]), this.bs.ng("effector", this.side, this.chain, "01"))
            if(this.mirrored):
                pmc.scale(this.globalMoveGrp, [-1,-1,-1])
                pmc.scale(this.globalMove, [1,1,1])
                # pmc.scale(grps[0], [1,1,-1])
                

        def makeNodes():
            staticDist = 0
            for jt in this.ikJts[1:]:
                x, y, z = pmc.xform(jt, q=1, t=1)
                staticDist += x

            # d.nodeName("decomp", "GlobalScale", this.chain, side = this.side)
                
            scaleDecomp = pmc.shadingNode("decomposeMatrix", au=1, n=d.nodeName("decomp", "globalScale", this.chain, side = this.side))
            # scaleDecomp = pmc.shadingNode("decomposeMatrix", au=1, n=this.bs.ng(
            #     "decomp", "globalScale", this.side, this.chain))
            nudgeA = pmc.shadingNode("addDoubleLinear", au=1, n=d.nodeName("aDL", "nudge", this.chain, side = this.side))
            fullLen = pmc.shadingNode("multDoubleLinear", au=1, n=d.nodeName("mDL", "fullDist", this.chain, side = this.side))
            nudgeM = pmc.shadingNode("multDoubleLinear", au=1, n=d.nodeName("mDL", "nudge", this.chain, side = this.side))
            scaleM = pmc.shadingNode("multDoubleLinear", au=1, n=d.nodeName("mDL", "scaleOffset", this.chain, side = this.side))

            divA = pmc.shadingNode("multiplyDivide", au=1, n=d.nodeName("divA", "stretchDistVal", this.chain, side = this.side))

            stretchCond = pmc.shadingNode("condition", au=1, n=d.nodeName("cond", "stretch", this.chain, side = this.side))

            dynamicDist = pmc.shadingNode("distanceBetween", au=1, n=d.nodeName("dist", "dynamic", this.chain, side = this.side))
            blendA = pmc.shadingNode("blendTwoAttr", au=1, n=d.nodeName("bTA", this.chain, side = this.side))

            pmc.select(scaleDecomp)
            pmc.connectAttr(this.bs.ag(pmc.listRelatives(this.globalMove, c=1)[
                            0], "parentMatrix[0]"), this.bs.ag(scaleDecomp, "inputMatrix"))
            pmc.connectAttr(this.bs.ag(scaleDecomp, "outputScaleX"),
                            this.bs.ag(fullLen, "input2"))

            fullLen.attr("input1").set(staticDist)

            pmc.connectAttr(this.bs.ag(this.startCC[0], "worldMatrix"),
                            this.bs.ag(dynamicDist, "inMatrix1"))
            pmc.connectAttr(this.bs.ag(this.endCC[0], "worldMatrix"),
                            this.bs.ag(dynamicDist, "inMatrix2"))

            pmc.connectAttr(this.bs.ag(dynamicDist, "distance"), this.bs.ag(divA, "input1X"))
            pmc.connectAttr(this.bs.ag(fullLen, "output"), this.bs.ag(divA, "input2X"))
            divA.attr("operation").set(2)

            pmc.connectAttr(this.bs.ag(fullLen, "output"),
                            this.bs.ag(stretchCond, "secondTerm"))
            pmc.connectAttr(this.bs.ag(divA, "outputX"), this.bs.ag(
                stretchCond, "colorIfTrueR"))
            pmc.connectAttr(this.bs.ag(dynamicDist, "distance"),
                            this.bs.ag(stretchCond, "firstTerm"))
            stretchCond.attr("operation").set(2)

            pmc.connectAttr(this.bs.ag(stretchCond, "outColorR"),
                            this.bs.ag(blendA, "input[1]"))
            blendA.attr("input[0]").set(1)
            pmc.connectAttr(this.bs.ag(this.endCC[0], "Stretchy"),
                            this.bs.ag(blendA, "attributesBlender"))

            pmc.connectAttr(this.bs.ag(this.endCC[0], "Nudge"),
                            this.bs.ag(nudgeM, "input1"))
            pmc.connectAttr(this.bs.ag(this.endCC[0], "NudgeMultiplier"),
                            this.bs.ag(nudgeM, "input2"))

            pmc.connectAttr(this.bs.ag(nudgeM, "output"),
                            this.bs.ag(nudgeA, "input1"))
            pmc.connectAttr(this.bs.ag(blendA, "output"),
                            this.bs.ag(nudgeA, "input2"))

            pmc.connectAttr(this.bs.ag(nudgeA, "output"),
                            this.bs.ag(scaleM, "input1"))
            pmc.connectAttr(this.bs.ag(scaleDecomp, "outputScaleX"),
                            this.bs.ag(scaleM, "input2"))

            for index, jt in enumerate(this.ikJts[1:]):
                finalA = pmc.shadingNode("multDoubleLinear", au=1, n=d.nodeName("mDL", index, this.chain, side = this.side))
                trans = jt.attr("translateX").get()
                finalA.attr("input1").set(trans)
                pmc.connectAttr(this.bs.ag(scaleM, "output"), this.bs.ag(finalA, "input2"))
                pmc.connectAttr(this.bs.ag(finalA, "output"),
                                this.bs.ag(jt, 'translateX'), f=1)
        makeCCs()
        makeNodes()

    def makeFK(this):

        this.fkJts = pmc.duplicate(this.baseJts)
        
        for index, jt in enumerate(this.fkJts):
            pmc.rename(jt, d.fkName(this.names[index], side=this.side))
            pmc.setAttr(str(jt) + ".radius", this.radiusArr[1])
            # Make Circle
            
            this.fkCC = pmc.circle(
                r=1, n=d.ccName("FK", this.names[index], side=this.side))[0]
            d.setCCColorBySide(this.fkCC, side=this.side)
            temp = pmc.spaceLocator(n='temp')
            if index == 0:
                    pmc.parent([this.fkCC, temp], this.globalMove)
            else:
                pmc.parent([this.fkCC, temp], pmc.ls(
                    d.fkName(this.names[index-1], side=this.side)))
    
            # if index > 0:
            #     pmc.parent(jt, this.fkJts[index - 1])
            this.fkCCs.append(this.fkCC)
            pmc.connectAttr(str(temp) + ".matrix",
                            str(this.fkCC) + ".offsetParentMatrix")
            pmc.delete(pmc.parentConstraint(jt, temp))
            pmc.delete(temp)
            pmc.makeIdentity(this.fkCC, t=1, r=1, s=1)
            if(this.mirrored):
                this.fkOffset = pmc.group(this.fkCC, n = this.bs.ng("grpOffset", this.side, this.chain,this.names[index], "FKMirror01"))
                pmc.move(this.bs.ag(this.fkOffset, "scalePivot"), pmc.xform(this.fkCC, ws=1, t=1, q=1))
                pmc.move(this.bs.ag(this.fkOffset, "rotatePivot"), pmc.xform(this.fkCC, ws=1, t=1, q=1))
                if(index % 2 != 0):    
                    pmc.scale(this.fkOffset, [1,1,-1])
                if(index == 0):
                    pmc.parent(this.fkOffset, this.globalMove)
            
            pmc.rotate(this.fkCC + ".cv[*]", [90, 90, 90], r=1)
            pmc.orientConstraint(this.fkCC, jt, mo=1)

        jtGrp = pmc.group(this.fkJts[0], n=d.ng(
            "grp",this.chain, "FK"))
        pmc.parent(jtGrp, this.g_joint)


        pmc.scaleConstraint(this.globalMove, jtGrp, mo=1)

    def makeBind(this):
        this.bindJts = pmc.duplicate(this.baseJts)
        # pmc.delete(pmc.listRelatives(this.bindJts[-2], children=1)[-1])
        pmc.delete(pmc.listRelatives(this.bindJts[-1], children=1))
        # pmc.delete(pmc.listRelatives(this.bindJts[-2],q children=1))
        for index, jt in enumerate(this.bindJts):
            pmc.rename(jt, d.bindName(this.names[index], side = this.side))
            pmc.setAttr(str(jt) + ".radius", this.radiusArr[2])

        pmc.parent(pmc.group(this.bindJts[0], n=d.ng(
            "grp",this.chain, "bind")), this.g_joint)
        # pmc.pointConstraint(this.globalMove[0], this.bindJts[0])

    def makeScale(this):
        # ik scale is already in place
        # jusst need to handle fk
        for index, cc in enumerate(this.fkCCs):
            pmc.pointConstraint(
                cc if index == 0 else this.fkJts[index], this.fkJts[index] if index == 0 else cc)
            if index >= len(this.fkCCs)-1:
                continue
            cc.addAttr(this.bs.ng(this.names[index], "FKStretch"),
                       defaultValue=0, h=0, k=1, r=1, w=1)
            add = pmc.shadingNode("addDoubleLinear", au=1, n=this.bs.ng(
                "aDL", this.names[index], this.side, this.chain))
            multA = pmc.shadingNode("multDoubleLinear", au=1, n=this.bs.ng(
                "mDLA",  this.names[index], this.side, this.chain))
            multB = pmc.shadingNode("multDoubleLinear", au=1, n=this.bs.ng(
                "mDLB",  this.names[index], this.side, this.chain))
            dist = this.fkJts[index + 1].attr("translateX").get()
            multA.attr("input1").set(dist)
            multA.attr("input2").set(1)
            multB.attr("input2").set(.1)
            pmc.connectAttr(
                str(this.fkCCs[index]) + "." + this.bs.ng(this.names[index], "FKStretch"), this.bs.ag(multB, "input1"))
            pmc.connectAttr(this.bs.ag(multA, "output"), this.bs.ag(add, "input2"))
            pmc.connectAttr(this.bs.ag(multB, "output"), this.bs.ag(add, "input1"))
            pmc.connectAttr(this.bs.ag(add, 'output'), this.bs.ag(
                this.fkJts[index + 1], "translateX"))

    def makeBlend(this):
        rang = pmc.shadingNode(
            "setRange", au=1, n="rang_" + this.chain +this.side + "_IkFKDriver01")
        if (not this.driverCC):
            this.driverCC = pmc.curve(d=1, p=[[0.0, 0.5672010183334351, 0.0], [-2.9993326933208664e-08, -0.5672010183334351, 0.6861673593521118], [0.6861673593521118, -0.5672010183334351, 0.0], [0.0, 0.5672010183334351, 0.0], [0, 2, 0], [0.0, 0.5672010183334351, 0.0], [8.997997724691231e-08, -0.5672010183334351, -0.6861673593521118], [0.6861673593521118, -0.5672010183334351, 0.0], [
                                      8.997997724691231e-08, -0.5672010183334351, -0.6861673593521118], [-0.6861673593521118, -0.5672010183334351, -5.998665386641733e-08], [0.0, 0.5672010183334351, 0.0], [-0.6861673593521118, -0.5672010183334351, -5.998665386641733e-08], [-2.9993326933208664e-08, -0.5672010183334351, 0.6861673593521118]], k=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], n=this.bs.ng("anim", this.side, this.chain, "misc01"))
            pmc.scale(this.driverCC, [1 *this.bs.joint_radius, 2 *this.bs.joint_radius, 1 *this.bs.joint_radius], os=1)
            pmc.makeIdentity(this.driverCC, a=1, t=1, r=1, s=1)
            pmc.parent(this.driverCC, this.bindJts[-1])
            # place driverCC
            pmc.delete(pmc.pointConstraint(this.ikJts[0], this.driverCC))
            pmc.delete(pmc.aimConstraint(
                this.ikJts[-1], this.driverCC, aim=(0, 1, 0)))
            x, y, z = pmc.xform(
                this.bs.ag(this.ikJts[-1], "scalePivot"), q=1, t=1, ws=1)
            pmc.move(x, y, z, this.bs.ag(this.driverCC, "scalePivot"), ws=1, )
            pmc.move(x, y, z, this.bs.ag(this.driverCC, "rotatePivot"), ws=1, )
            pmc.scale(this.driverCC, -1, -.5, -1, os=1)
            pmc.makeIdentity(this.driverCC, a=1, t=1, r=1, s=1)
            pmc.parent(this.driverCC, this.ccs)
            pmc.parentConstraint(this.bindJts[-1], this.driverCC)
            x, y, z = pmc.xform(
                this.bs.ag(this.bindJts[-1], "rotatePivot"), q=1, t=1, ws=1)
            pmc.move(this.bs.ag(this.driverCC, "cv[4]"), [x, y, z], ws=1)

        this.driverCC.addAttr(this.chain + "IKFK", max=1, min=0,
                              defaultValue=d.p_arm_IKFKDefault, h=0, k=1, r=1, w=1)
        pmc.connectAttr(str(this.driverCC) + "."+this.chain + "IKFK",
                        str(rang) + ".valueX")
        pmc.connectAttr(str(this.driverCC) + "."+this.chain + "IKFK",
                        str(rang) + ".valueY")
        rang.attr("minY").set(1)
        rang.attr("maxX").set(1)
        rang.attr("oldMaxX").set(1)
        rang.attr("oldMaxY").set(1)
        for index, jt in enumerate(this.bindJts):
            ori = (pmc.orientConstraint(
                this.ikJts[index], this.fkJts[index], this.bindJts[index]))
            pmc.connectAttr(this.bs.ag(rang, "outValueX"), this.bs.ag(
                ori, this.fkJts[index] + "W1"))
            pmc.connectAttr(this.bs.ag(rang, "outValueY"), this.bs.ag(
                ori, this.ikJts[index] + "W0"))
            pmc.connectAttr(rang + ".outValueX",
                            str(this.fkCCs[index]) + ".visibility")
            if index == 0:
                point = pmc.pointConstraint(
                    this.fkJts[0], this.ikJts[0], jt)
                point = pmc.pointConstraint(point, q=1, wal=1)
                pmc.connectAttr(this.bs.ag(rang, "outValueX"), point[0])
                pmc.connectAttr(this.bs.ag(rang, "outValueY"), point[1])
                continue

            blend = pmc.shadingNode('blendTwoAttr', au=1, n=this.bs.ng(
                "bta", this.side, this.names[index] + "01"))
            pmc.connectAttr(this.bs.ag(rang, "outValueX"),
                            this.bs.ag(blend, "attributesBlender"))
            pmc.connectAttr(this.bs.ag(this.fkJts[index], "translateX"), this.bs.ag(
                blend, "input[1]"))
            pmc.connectAttr(this.bs.ag(this.ikJts[index], "translateX"), this.bs.ag(
                blend, "input[0]"))
            pmc.connectAttr(this.bs.ag(blend, "output"), this.bs.ag(
                this.bindJts[index], "translateX"))

        pmc.connectAttr(rang + ".outValueY",
                        str(this.startCC[0]) + ".visibility")
        pmc.connectAttr(rang + ".outValueY",
                        str(this.pvCurve) + ".visibility")
        pmc.connectAttr(rang + ".outValueY",
                        str(this.pvCC) + ".visibility")
        
    def houseKeeping(this):
        # handle global move
        ikGrp = pmc.ls(pmc.pickWalk(this.startCC[0], direction="up")[0])[0]
        # pmc.parent([ikGrp, this.fkCCs[0]], this.globalMove[0])
        pmc.parent([ikGrp], this.globalMove[0])
        temp = pmc.parentConstraint(this.targetJts[0], this.globalMoveGrp)
 
        # pmc.parent([pmc.pickWalk(this.startCC[0], direction="up")[0], pmc.pickWalk(
        #     this.fkCCs[0], direction="up")[0]], this.globalMove)

        # cleanup cc attrs

        for cc in this.fkCCs:
            this.bs.attrCleanup(cc, ["t", "s", "v"])

        this.bs.attrCleanup(this.startCC[0], ["r", "s", "v"])
        this.bs.attrCleanup(this.endCC[0], ["s", "v"])
        this.bs.attrCleanup(this.driverCC)
        this.bs.attrCleanup(this.pvCurve)
        this.bs.attrCleanup(this.pvCC, ["r",  "s", "v"])

        ls = pmc.ls("*" + this.side + "_" + this.chain + "*", type=this.bs.cleanupList)
        for cc in this.fkCCs + [this.startCC[0], this.endCC[0], this.pvCC, this.driverCC]:
            ls = ls + pmc.listConnections(cc)
            for out in ls:
                out.attr("ihi").set(0)

        pmc.delete(this.baseJts)

        # # update cc size based off reaycasting in 4 directions
        # this.radius = None
        # for cc in this.fkCCs:
        #     radius =d.getColumnRadius(d.p_skinName, cc) 
        #     if(radius):
        #         pmc.scale(pmc.listRelatives(cc)[0] + ".cv[*]",[radius, radius, radius], r=1)
        #         this.radius = radius
        #         continue
        #     if(this.radius):
        #         pmc.scale(pmc.listRelatives(cc)[0] + ".cv[*]",[this.radius, this.radius, this.radius], r=1)
        #         continue
        # d.getColumnRadius(d.p_skinName, this.fkCCs[0])
        for cc in this.fkCCs:
            d.makeCCShape(d.p_skinName, cc)

    def execute(this):
        
        this.initChains()
        this.makeIK()
        this.makeFK()
        this.makeBind()
        this.makeScale()
        this.makeBlend()
        this.houseKeeping()

        # pmc.select(this.targetJts)
        # print("Rig Completed")



