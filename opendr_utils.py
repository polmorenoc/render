__author__ = 'pol'

import opendr
import chumpy as ch
import geometry
import bpy
import mathutils
import numpy as np
from math import radians
from opendr.camera import ProjectPoints
from opendr.renderer import TexturedRenderer
from opendr.lighting import SphericalHarmonics
from opendr.lighting import LambertianPointLight
import ipdb
import light_probes
import scene_io_utils
from blender_utils import *
import imageio
import chumpy as ch
from chumpy import depends_on, Ch
import scipy.sparse as sp

class TheanoFunOnOpenDR(Ch):
    terms = 'theano_fun', 'theano_grad_fun'
    dterms = 'opendr_x'

    def compute_r(self):

        x = self.opendr_x.r
        return self.theano_fun(x)

    def compute_dr_wrt(self,wrt):
        if self.opendr_x is wrt:
            jac = self.theano_grad_fun(self.opendr_x)
            return sp.csc_matrix(jac)

<<<<<<< HEAD
def SHProjection(envMap, shCoefficients):


    #Backprojected.
    phis = 2*ch.pi*np.tile((np.roll(np.arange(envMap.shape[1])[::-1], np.int(envMap.shape[1]/2))/envMap.shape[1]).reshape([1,envMap.shape[1],1]), [envMap.shape[0],1,3])
    thetas = np.pi*np.tile((np.arange(envMap.shape[0])/envMap.shape[0]).reshape([envMap.shape[0],1,1]), [1,envMap.shape[1],3])

    phis = np.mod(phis, 2*np.pi)

    normalize = 1
    spherical_harmonics_coeffs = light_probes.spherical_harmonics_coeffs

    pEnvMap = np.zeros([envMap.shape[0],envMap.shape[1], 3, 9] )
    pEnvMap[:,:,:,0] = shCoefficients[0].reshape([1,1,3]) *  spherical_harmonics_coeffs[0]  * normalize
    pEnvMap[:,:,:,1] = shCoefficients[1].reshape([1,1,3]) * spherical_harmonics_coeffs[1]*np.sin(thetas) * np.cos(phis) * normalize
    pEnvMap[:,:,:,2] = shCoefficients[2].reshape([1,1,3]) * spherical_harmonics_coeffs[2]*np.cos(thetas) * normalize
    pEnvMap[:,:,:,3] = shCoefficients[3].reshape([1,1,3]) * spherical_harmonics_coeffs[3]*np.sin(thetas)*np.sin(phis) * normalize
    pEnvMap[:,:,:,4] = shCoefficients[4].reshape([1,1,3]) * spherical_harmonics_coeffs[4]*np.sin(thetas) * np.cos(phis) * np.sin(phis)* np.sin(thetas)  * normalize
    pEnvMap[:,:,:,5] = shCoefficients[5].reshape([1,1,3]) * spherical_harmonics_coeffs[5]*np.sin(thetas) * np.sin(phis) * np.cos(thetas)  * normalize
    pEnvMap[:,:,:,6] = shCoefficients[6].reshape([1,1,3]) * spherical_harmonics_coeffs[6]*(3 * np.cos(thetas)**2 - 1) * noxrmalize
    pEnvMap[:,:,:,7] = shCoefficients[7].reshape([1,1,3]) * spherical_harmonics_coeffs[7]*np.sin(thetas) * np.cos(phis) * np.cos(thetas) * normalize
    pEnvMap[:,:,:,8] = shCoefficients[8].reshape([1,1,3]) * spherical_harmonics_coeffs[8]*(((np.sin(thetas) * np.cos(phis)) ** 2) - ((np.sin(thetas) * np.sin(phis)) ** 2)) * normalize

    return pEnvMap

def SHSpherePlot():
    #Visualize plots
    ignoreEnvMaps = np.loadtxt('data/bad_envmaps.txt')
    envMapDic = {}
    SHFilename = 'data/LightSHCoefficients.pickle'

    with open(SHFilename, 'rb') as pfile:
        envMapDic = pickle.load(pfile)

    hdritems = list(envMapDic.items())[0:10]

    pEnvMapsList = []
    envMapsList = []
    width = 600
    height = 300
    for hdrFile, hdrValues in hdritems:

        hdridx = hdrValues[0]
        if hdridx not in ignoreEnvMaps:
            if not os.path.exists('light_probes/envMap' + str(hdridx)):
                os.makedirs('light_probes/envMap' + str(hdridx))

            envMapCoeffs = hdrValues[1]
            envMap = np.array(imageio.imread(hdrFile))[:,:,0:3]
            # normalize = envMap.mean()*envMap.shape[0]*envMap.shape[1]
            # envMap = 0.3*envMap[:,:,0] + 0.59*envMap[:,:,1] + 0.11*envMap[:,:,2]
            # if envMap.shape[0] != height or envMap.shape[1] != width:
            envMap = cv2.resize(src=envMap, dsize=(width,height))

            print("Processing hdridx" + str(hdridx))
            # envMapCoeffs = 0.3*envMapCoeffs[:,0] + 0.59*envMapCoeffs[:,1] + 0.11*envMapCoeffs[:,2]
            # envMapCoeffs *= normalize
            # pEnvMap = SHProjection(envMap, envMapCoeffs)
            envMapMean = envMap.mean()

            envMapCoeffs2 = light_probes.getEnvironmentMapCoefficients(envMap, 1, 0, 'equirectangular')
            # envMapCoeffs2 = 0.3*envMapCoeffs2[:,0] + 0.59*envMapCoeffs2[:,1] + 0.11*envMapCoeffs2[:,2]
            pEnvMap = SHProjection(envMap, envMapCoeffs2)

            tm = cv2.createTonemapDrago(gamma=2.2)
            tmEnvMap = tm.process(envMap)
            cv2.imwrite('light_probes/envMap' + str(hdridx) + '/texture.jpeg' , 255*tmEnvMap[:,:,[2,1,0]])
            approxProjections = []
            for coeffApprox in np.arange(9) + 1:
                approxProjection = np.sum(pEnvMap[:,:,:,0:coeffApprox], axis=3)
                approxProjectionPos =  approxProjection.copy()
                approxProjectionPos[approxProjection<0] = 0
                # tm = cv2.createTonemapDrago(gamma=2.2)
                # tmApproxProjection = tm.process(approxProjection)
                approxProjections = approxProjections + [approxProjection[None, :,:,:,None]]
                cv2.imwrite('light_probes/envMap' + str(hdridx) + '/approx' + str(coeffApprox-1) + '.jpeg', 255 * approxProjectionPos[:,:,[2,1,0]])
            approxProjections = np.concatenate(approxProjections, axis=4)
            pEnvMapsList = pEnvMapsList + [approxProjections]

            envMapsList = envMapsList + [envMap[None,:,:,:]]

    pEnvMaps = np.concatenate(pEnvMapsList, axis=0)
    envMaps = np.concatenate(envMapsList, axis=0)

    #Total sum of squares
    envMapsMean = np.mean(envMaps, axis=0)
    pEnvMapsMean = np.mean(pEnvMaps, axis=0)

    tsq = np.sum((envMaps - envMapsMean)**2)/(envMapsMean.shape[0]*envMapsMean.shape[1])

    ess = np.sum((pEnvMaps - envMapsMean[None,:,:,:,None])**2, axis=(0,1,2,3))/(envMapsMean.shape[0]*envMapsMean.shape[1])

    uess = np.sum((pEnvMaps - envMaps[:,:,:,:,None])**2, axis=(0,1,2,3))/(envMapsMean.shape[0]*envMapsMean.shape[1])

    explainedVar = ess/tsq

    tsq2 = uess + ess

    ipdb.set_trace()

    #Do something with standardized residuals.
    stdres = (pEnvMaps - pEnvMapsMean)/np.sqrt(np.sum((pEnvMaps - pEnvMapsMean)**2,axis=0))

    return explainedVar

=======
>>>>>>> db1126c63c803bf4417236518d69fb07a7000730

def exportEnvMapSHImages(shCoeffsRGB, useBlender, scene, width, height, rendererGT):
    import glob
    for hdridx, hdrFile in enumerate(glob.glob("data/hdr/dataset/*")):

        envMapFilename = hdrFile
        envMapTexture = np.array(imageio.imread(envMapFilename))[:,:,0:3]
        phiOffset = 0

        phiOffsets = [0, np.pi/2, np.pi, 3*np.pi/2]
        # phiOffsets = [0, np.pi/2, np.pi, 3*np.pi/2]

        if not os.path.exists('light_probes/envMap' + str(hdridx)):
            os.makedirs('light_probes/envMap' + str(hdridx))

        cv2.imwrite('light_probes/envMap' + str(hdridx) + '/texture.png' , 255*envMapTexture[:,:,[2,1,0]])

        for phiOffset in phiOffsets:
            envMapMean = envMapTexture.mean()
            envMapCoeffs = light_probes.getEnvironmentMapCoefficients(envMapTexture, envMapMean, -phiOffset, 'equirectangular')
            shCoeffsRGB[:] = envMapCoeffs
            if useBlender:
                updateEnviornmentMap(envMapFilename, scene)
                setEnviornmentMapStrength(0.3/envMapMean, scene)
                rotateEnviornmentMap(phiOffset, scene)

            scene.render.filepath = 'light_probes/envMap' + str(hdridx) + '/blender_' + str(np.int(180*phiOffset/np.pi)) + '.png'
            bpy.ops.render.render(write_still=True)
            cv2.imwrite('light_probes/envMap' + str(hdridx) + '/opendr_' + str(np.int(180*phiOffset/np.pi)) + '.png' , 255*rendererGT.r[:,:,[2,1,0]])


def exportEnvMapSHLightCoefficients():
    import glob
    envMapDic = {}
    hdrs = glob.glob("data/hdr/dataset/*")
    hdrstorender = hdrs

    for hdridx, hdrFile in enumerate(hdrstorender):
        print("Processing env map" + str(hdridx))
        envMapFilename = hdrFile
        envMapTexture = np.array(imageio.imread(envMapFilename))[:,:,0:3]
        phiOffset = 0

        if not os.path.exists('light_probes/envMap' + str(hdridx)):
            os.makedirs('light_probes/envMap' + str(hdridx))

        # cv2.imwrite('light_probes/envMap' + str(hdridx) + '/texture.png' , 255*envMapTexture[:,:,[2,1,0]])

        envMapMean = envMapTexture.mean()

        envMapCoeffs = light_probes.getEnvironmentMapCoefficients(envMapTexture, envMapMean, phiOffset, 'equirectangular')

        envMapDic[hdrFile] = [hdridx, envMapCoeffs]

    SHFilename = 'data/LightSHCoefficients.pickle'
    with open(SHFilename, 'wb') as pfile:
        pickle.dump(envMapDic, pfile)


def createRendererTarget(glMode, chAz, chObjAz, chEl, chDist, center, v, vc, f_list, vn, light_color, chComponent, chVColors, targetPosition, chDisplacement, chScale, width,height, uv, haveTextures_list, textures_list, frustum, win ):
    renderer = TexturedRenderer()
    renderer.set(glMode=glMode)

    vflat = [item.copy() for sublist in v for item in sublist]
    rangeMeshes = range(len(vflat))

    scaleMat = geometry.Scale(x=chScale[0], y=chScale[1],z=chScale[2])[0:3,0:3]
    chRotAzMat = geometry.RotateZ(a=-chObjAz)[0:3,0:3]
    transformation = ch.dot(chRotAzMat, scaleMat)
    invTranspModel = np.transpose(np.linalg.inv(transformation))

    vch = [ch.dot(ch.array(vflat[mesh]),transformation) + targetPosition for mesh in rangeMeshes]

    if len(vch)==1:
        vstack = vch[0]
    else:
        vstack = ch.vstack(vch)

    camera, modelRotation = setupCamera(vstack, chAz, chEl, chDist, center + targetPosition + chDisplacement, width, height)
    vnflat = [item for sublist in vn for item in sublist]

    vnch = [ch.array(vnflat[mesh]) for mesh in rangeMeshes]
    vnch = [ch.dot(ch.array(vnflat[mesh]),invTranspModel) for mesh in rangeMeshes]
    vnchnorm = [vnch[mesh]/ch.sqrt(vnch[mesh][:,0]**2 + vnch[mesh][:,1]**2 + vnch[mesh][:,2]**2).reshape([-1,1]) for mesh in rangeMeshes]
    vcflat = [item for sublist in vc for item in sublist]
    vcch = [np.ones_like(vcflat[mesh])*chVColors.reshape([1,3]) for mesh in rangeMeshes]
    # vcch = [ch.array(vcflat[mesh]) for mesh in rangeMeshes]

    vc_list = computeSphericalHarmonics(vnchnorm, vcch, light_color, chComponent)
    # vc_list =  computeGlobalAndPointLighting(vch, vnch, vcch, lightPosGT, chGlobalConstantGT, light_colorGT)


    setupTexturedRenderer(renderer, vstack, vch, f_list, vc_list, vnchnorm,  uv, haveTextures_list, textures_list, camera, frustum, win)
    return renderer


def createRendererGT(glMode, chAz, chObjAz, chEl, chDist, center, v, vc, f_list, vn, light_color, chComponent, chVColors, targetPosition, chDisplacement, chScale, width,height, uv, haveTextures_list, textures_list, frustum, win ):
    renderer = TexturedRenderer()
    renderer.set(glMode=glMode)

    scaleMat = geometry.Scale(x=chScale[0], y=chScale[1],z=chScale[2])[0:3,0:3]
    chRotAzMat = geometry.RotateZ(a=-chObjAz)[0:3,0:3]
    transformation = ch.dot(chRotAzMat, scaleMat)
    invTranspModel = ch.transpose(ch.inv(transformation))

    vflat = [item for sublist in v for item in sublist]
    rangeMeshes = range(len(vflat))
    vch = [ch.array(vflat[mesh]) for mesh in rangeMeshes]
    vch[0] = ch.dot(vch[0], transformation) + targetPosition
    if len(vch)==1:
        vstack = vch[0]
    else:
        vstack = ch.vstack(vch)

    camera, modelRotation = setupCamera(vstack, chAz, chEl, chDist, center + targetPosition + chDisplacement, width, height)
    vnflat = [item for sublist in vn for item in sublist]
    vnch = [ch.array(vnflat[mesh]) for mesh in rangeMeshes]
    vnch[0] = ch.dot(vnch[0], invTranspModel)
    vnchnorm = [vnch[mesh]/ch.sqrt(vnch[mesh][:,0]**2 + vnch[mesh][:,1]**2 + vnch[mesh][:,2]**2).reshape([-1,1]) for mesh in rangeMeshes]
    vcflat = [item for sublist in vc for item in sublist]
    vcch = [ch.array(vcflat[mesh]) for mesh in rangeMeshes]
    vcch[0] = np.ones_like(vcflat[0])*chVColors.reshape([1,3])
    # vcch[0] = vcflat[0]

    vc_list = computeSphericalHarmonics(vnchnorm, vcch, light_color, chComponent)
    # vc_list =  computeGlobalAndPointLighting(vch, vnch, vcch, lightPosGT, chGlobalConstantGT, light_colorGT)

    setupTexturedRenderer(renderer, vstack, vch, f_list, vc_list, vnchnorm,  uv, haveTextures_list, textures_list, camera, frustum, win)
    return renderer

#Old method
def generateSceneImages(width, height, envMapFilename, envMapMean, phiOffset, chAzGT, chElGT, chDistGT, light_colorGT, chComponentGT, glMode):
    replaceableScenesFile = '../databaseFull/fields/scene_replaceables_backup.txt'
    sceneLines = [line.strip() for line in open(replaceableScenesFile)]
    for sceneIdx in np.arange(len(sceneLines)):
        sceneNumber, sceneFileName, instances, roomName, roomInstanceNum, targetIndices, targetPositions = scene_io_utils.getSceneInformation(sceneIdx, replaceableScenesFile)
        sceneDicFile = 'data/scene' + str(sceneNumber) + '.pickle'
        bpy.ops.wm.read_factory_settings()
        scene_io_utils.loadSceneBlendData(sceneIdx, replaceableScenesFile)
        scene = bpy.data.scenes['Main Scene']
        bpy.context.screen.scene = scene
        scene_io_utils.setupScene(scene, roomInstanceNum, scene.world, scene.camera, width, height, 16, True, False)
        scene.update()
        scene.render.resolution_x = width #perhaps set resolution in code
        scene.render.resolution_y = height
        scene.render.tile_x = height/2
        scene.render.tile_y = width
        scene.cycles.samples = 100
        addEnvironmentMapWorld(envMapFilename, scene)
        setEnviornmentMapStrength(0.3/envMapMean, scene)
        rotateEnviornmentMap(phiOffset, scene)

        if not os.path.exists('scenes/' + str(sceneNumber)):
            os.makedirs('scenes/' + str(sceneNumber))
        for targetIdx, targetIndex in enumerate(targetIndices):
            targetPosition = targetPositions[targetIdx]

            rendererGT.clear()
            del rendererGT

            v, f_list, vc, vn, uv, haveTextures_list, textures_list = scene_io_utils.loadSavedScene(sceneDicFile)
            # removeObjectData(targetIndex, v, f_list, vc, vn, uv, haveTextures_list, textures_list)
            # addObjectData(v, f_list, vc, vn, uv, haveTextures_list, textures_list,  v_teapots[currentTeapotModel][0], f_list_teapots[currentTeapotModel][0], vc_teapots[currentTeapotModel][0], vn_teapots[currentTeapotModel][0], uv_teapots[currentTeapotModel][0], haveTextures_list_teapots[currentTeapotModel][0], textures_list_teapots[currentTeapotModel][0])
            vflat = [item for sublist in v for item in sublist]
            rangeMeshes = range(len(vflat))
            vch = [ch.array(vflat[mesh]) for mesh in rangeMeshes]
            # vch[0] = ch.dot(vch[0], scaleMatGT) + targetPosition
            if len(vch)==1:
                vstack = vch[0]
            else:
                vstack = ch.vstack(vch)
            cameraGT, modelRotationGT = setupCamera(vstack, chAzGT, chElGT, chDistGT, targetPosition, width, height)
            # cameraGT, modelRotationGT = setupCamera(vstack, chAzGT, chElGT, chDistGT, center + targetPosition, width, height)
            vnflat = [item for sublist in vn for item in sublist]
            vnch = [ch.array(vnflat[mesh]) for mesh in rangeMeshes]
            vnchnorm = [vnch[mesh]/ch.sqrt(vnch[mesh][:,0]**2 + vnch[mesh][:,1]**2 + vnch[mesh][:,2]**2).reshape([-1,1]) for mesh in rangeMeshes]
            vcflat = [item for sublist in vc for item in sublist]
            vcch = [ch.array(vcflat[mesh]) for mesh in rangeMeshes]
            vc_list = computeSphericalHarmonics(vnchnorm, vcch, light_colorGT, chComponentGT)

            rendererGT = TexturedRenderer()
            rendererGT.set(glMode=glMode)
            setupTexturedRenderer(rendererGT, vstack, vch, f_list, vc_list, vnchnorm,  uv, haveTextures_list, textures_list, cameraGT, frustum, win)
            cv2.imwrite('scenes/' + str(sceneNumber) + '/opendr_' + str(targetIndex) + '.png' , 255*rendererGT.r[:,:,[2,1,0]])

            placeCamera(scene.camera, -chAzGT[0].r*180/np.pi, chElGT[0].r*180/np.pi, chDistGT, targetPosition)
            scene.update()
            scene.render.filepath = 'scenes/' + str(sceneNumber) + '/blender_' + str(targetIndex) + '.png'
            bpy.ops.render.render(write_still=True)



def getOcclusionFraction(renderer):
    vis_occluded = np.array(renderer.indices_image==1).copy().astype(np.bool)
    vis_im = np.array(renderer.image_mesh_bool([0])).copy().astype(np.bool)

    return 1. - np.sum(vis_occluded)/np.sum(vis_im)

#From http://www.ppsloan.org/publications/StupidSH36.pdf
def chZonalHarmonics(a):
    zl0 = -ch.sqrt(ch.pi)*(-1.0 + ch.cos(a))
    zl1 = 0.5*ch.sqrt(3.0*ch.pi)*ch.sin(a)**2
    zl2 = -0.5*ch.sqrt(5.0*ch.pi)*ch.cos(a)*(-1.0 + ch.cos(a))*(ch.cos(a)+1.0)
    z = [zl0, zl1, zl2]
    return ch.concatenate(z)

# http://cseweb.ucsd.edu/~ravir/papers/envmap/envmap.pdf
chSpherical_harmonics = {
    (0, 0): lambda theta, phi: ch.Ch([0.282095]),

    (1, -1): lambda theta, phi: 0.488603 * ch.sin(theta) * ch.sin(phi),
    (1, 0): lambda theta, phi: 0.488603 * ch.cos(theta),
    (1, 1): lambda theta, phi: 0.488603 * ch.sin(theta) * ch.cos(phi),

    (2, -2): lambda theta, phi: 1.092548 * ch.sin(theta) * ch.cos(phi) * ch.sin(theta) * ch.sin(phi),
    (2, -1): lambda theta, phi: 1.092548 * ch.sin(theta) * ch.sin(phi) * ch.cos(theta),
    (2, 0): lambda theta, phi: 0.315392 * (3 * ch.cos(theta)**2 - 1),
    (2, 1): lambda theta, phi: 1.092548 * ch.sin(theta) * ch.cos(phi) * ch.cos(theta),
    (2, 2): lambda theta, phi: 0.546274 * (((ch.sin(theta) * ch.cos(phi)) ** 2) - ((ch.sin(theta) * ch.sin(phi)) ** 2))
}

#From http://www.ppsloan.org/publications/StupidSH36.pdf
def chZonalToSphericalHarmonics(z, theta, phi):
    sphCoeffs = []
    for l in np.arange(len(z)):
        for m in np.arange(np.int(-(l*2+1)/2),np.int((l*2+1)/2) + 1):
            ylm_d = chSpherical_harmonics[(l,m)](theta,phi)
            sh = np.sqrt(4*np.pi/(2*l + 1))*z[l]*ylm_d
            sphCoeffs = sphCoeffs + [sh]

    #Correct order in band l=1.
    sphCoeffs[1],sphCoeffs[3] = sphCoeffs[3],sphCoeffs[1]
    chSphCoeffs = ch.concatenate(sphCoeffs)
    return chSphCoeffs

#From http://www.ppsloan.org/publications/StupidSH36.pdf
def clampedCosineCoefficients():

    constants = []
    for l in np.arange(3):
        for m in np.arange(np.int(-(l*2+1)/2),np.int((l*2+1)/2) + 1):
            normConstant = np.pi
            if l > 1 and l % 1 == 0:
                normConstant = 0
            if l == 1:
                normConstant = 2*np.pi/3
            if l > 1 and l % 2 == 0:
                normConstant = 2*np.pi*(((-1)**(l/2.-1.))/((l+2)*(l-1)))*(np.math.factorial(l)/((2**(l))*(np.math.factorial(l/2)**2)))
                # normConstant = 0.785398

            constants = constants + [normConstant]

    return np.array(constants)

def setupCamera(v, chAz, chEl, chDist, objCenter, width, height):

    chCamModelWorld = computeHemisphereTransformation(chAz, chEl, chDist, objCenter)

    chMVMat = ch.dot(chCamModelWorld, np.array(mathutils.Matrix.Rotation(radians(270), 4, 'X')))

    chInvCam = ch.inv(chMVMat)

    modelRotation = chInvCam[0:3,0:3]

    chRod = opendr.geometry.Rodrigues(rt=modelRotation).reshape(3)
    chTranslation = chInvCam[0:3,3]

    translation, rotation = (chTranslation, chRod)
    camera = ProjectPoints(v=v, rt=rotation, t=translation, f= 1.12*ch.array([width,width]), c=ch.array([width,height])/2.0, k=ch.zeros(5))
    camera.openglMat = np.array(mathutils.Matrix.Rotation(radians(180), 4, 'X'))
    return camera, modelRotation

def computeHemisphereTransformation(chAz, chEl, chDist, objCenter):

    chDistMat = geometry.Translate(x=ch.Ch(0), y=-chDist, z=ch.Ch(0))
    chToObjectTranslate = geometry.Translate(x=objCenter[0], y=objCenter[1], z=objCenter[2])

    chRotAzMat = geometry.RotateZ(a=chAz)
    chRotElMat = geometry.RotateX(a=-chEl)
    chCamModelWorld = ch.dot(chToObjectTranslate, ch.dot(chRotAzMat, ch.dot(chRotElMat,chDistMat)))

    return chCamModelWorld

def computeSphericalHarmonics(vn, vc, light_color, components):

    # vnflat = [item for sublist in vn for item in sublist]
    # vcflat = [item for sublist in vc for item in sublist]
    rangeMeshes = range(len(vn))
    A_list = [SphericalHarmonics(vn=vn[mesh],
                       components=components,
                       light_color=light_color) for mesh in rangeMeshes]

    vc_list = [A_list[mesh]*vc[mesh] for mesh in rangeMeshes]
    return vc_list

def computeGlobalAndPointLighting(v, vn, vc, light_pos, globalConstant, light_color):
    # Construct point light source
    rangeMeshes = range(len(vn))
    vc_list = []
    for mesh in rangeMeshes:
        l1 = LambertianPointLight(
            v=v[mesh],
            vn=vn[mesh],
            num_verts=len(v[mesh]),
            light_pos=light_pos,
            vc=vc[mesh],
            light_color=light_color)

        vcmesh = vc[mesh]*(l1 + globalConstant)
        vc_list = vc_list + [vcmesh]
    return vc_list

def setupTexturedRenderer(renderer, vstack, vch, f_list, vc_list, vnch, uv, haveTextures_list, textures_list, camera, frustum, sharedWin=None):

    f = []
    f_listflat = [item for sublist in f_list for item in sublist]

    for mesh in f_listflat:
        lenMeshes = len(f)
        for polygons in mesh:
            f = f + [polygons + lenMeshes]
    fstack = np.vstack(f)

    # vnflat = [item for sublist in vnch for item in sublist]
    if len(vnch)==1:
        vnstack = vnch[0]
    else:
        vnstack = ch.vstack(vnch)

    # vc_listflat = [item for sublist in vc_list for item in sublist]
    if len(vc_list)==1:
        vcstack = vc_list[0]
    else:
        vcstack = ch.vstack(vc_list)

    uvflat = [item for sublist in uv for item in sublist]
    ftstack = np.vstack(uvflat)

    texturesch = []
    textures_listflat = [item for sublist in textures_list for item in sublist]
    for texture_list in textures_listflat:
        if texture_list != None:
            for texture in texture_list:
                if texture != None:
                    texturesch = texturesch + [ch.array(texture)]

    if len(texturesch) == 0:
        texture_stack = ch.Ch([])
    elif len(texturesch) == 1:
        texture_stack = texturesch[0].ravel()
    else:
        texture_stack = ch.concatenate([tex.ravel() for tex in texturesch])

    haveTextures_listflat = [item for sublist in haveTextures_list for item in sublist]

    renderer.set(camera=camera, frustum=frustum, v=vstack, f=fstack, vn=vnstack, vc=vcstack, ft=ftstack, texture_stack=texture_stack, v_list=vch, f_list=f_listflat, vc_list=vc_list, ft_list=uvflat, textures_list=textures_listflat, haveUVs_list=haveTextures_listflat, bgcolor=ch.ones(3), overdraw=True)
    renderer.msaa = True
    renderer.sharedWin = sharedWin
    # renderer.clear()
    renderer.initGL()
    renderer.initGLTexture()


def addObjectData(v, f_list, vc, vn, uv, haveTextures_list, textures_list, vmod, fmod_list, vcmod, vnmod, uvmod, haveTexturesmod_list, texturesmod_list):
    v.insert(0,vmod)
    f_list.insert(0,fmod_list)
    vc.insert(0,vcmod)
    vn.insert(0,vnmod)
    uv.insert(0,uvmod)
    haveTextures_list.insert(0,haveTexturesmod_list)
    textures_list.insert(0,texturesmod_list)

def removeObjectData(objIdx, v, f_list, vc, vn, uv, haveTextures_list, textures_list):

    del v[objIdx]
    del f_list[objIdx]
    del vc[objIdx]
    del vn[objIdx]
    del uv[objIdx]
    del haveTextures_list[objIdx]
    del textures_list[objIdx]

