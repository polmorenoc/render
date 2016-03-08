test__author__ = 'pol'

import matplotlib
matplotlib.use('Qt4Agg')
import scene_io_utils
import mathutils
from math import radians
import timeit
import time
import opendr
import chumpy as ch
import geometry
import image_processing
import numpy as np
import cv2
import glfw
import generative_models
import recognition_models
import matplotlib.pyplot as plt
from opendr_utils import *
from utils import *
import OpenGL.GL as GL
import light_probes
from OpenGL import contextdata

plt.ion()

#########################################
# Test configuration
#########################################

seed = 1
np.random.seed(seed)

parameterRecognitionModels = set(['randForestAzs', 'randForestElevs', 'randForestVColors', 'linearRegressionVColors', 'neuralNetModelSHLight', ])
parameterRecognitionModels = set(['randForestAzs', 'randForestElevs', 'randForestVColors', 'linearRegressionVColors', 'linRegModelSHZernike' ])
parameterRecognitionModels = set(['randForestAzs', 'randForestElevs','linearRegressionVColors','neuralNetModelSHLight' ])
parameterRecognitionModels = set(['neuralNetPose', 'linearRegressionVColors','constantSHLight' ])
parameterRecognitionModels = set(['neuralNetPose', 'neuralNetApperanceAndLight', 'neuralNetVColors' ])
parameterRecognitionModels = set(['neuralNetPose', 'neuralNetModelSHLight', 'neuralNetVColors', 'neuralNetModelShape' ])
# parameterRecognitionModels = set(['neuralNetPose', 'neuralNetApperanceAndLight'])

# parameterRecognitionModels = set(['randForestAzs', 'randForestElevs','randForestVColors','randomForestSHZernike' ])

gtPrefix = 'train4_occlusion_shapemodel'
experimentPrefix = 'train4_occlusion_shapemodel_10k'
trainPrefixPose = 'train4_occlusion_shapemodel_10k'
trainPrefixVColor = 'train4_occlusion_shapemodel_10k'
trainPrefixLightCoeffs = 'train4_occlusion_shapemodel_10k'
trainPrefixShapeParams = 'train4_occlusion_shapemodel_10k'
trainModelsDirAppLight = 'train4_occlusion_shapemodel_10k'

#########################################
# OpenDR Initialization starts here
#########################################

#Main script options:

glModes = ['glfw','mesa']
glMode = glModes[0]

width, height = (150, 150)
win = -1

if glMode == 'glfw':
    #Initialize base GLFW context for the Demo and to share context among all renderers.
    glfw.init()
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    # glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.DEPTH_BITS,32)
    glfw.window_hint(glfw.VISIBLE, GL.GL_FALSE)
    win = glfw.create_window(width, height, "Demo",  None, None)
    glfw.make_context_current(win)

angle = 60 * 180 / np.pi
clip_start = 0.05
clip_end = 10
frustum = {'near': clip_start, 'far': clip_end, 'width': width, 'height': height}
camDistance = 0.4

teapots = [line.strip() for line in open('teapots.txt')]

# renderTeapotsList = np.arange(len(teapots))
renderTeapotsList = np.arange(len(teapots))[0:1]

targetModels = []

v_teapots, f_list_teapots, vc_teapots, vn_teapots, uv_teapots, haveTextures_list_teapots, textures_list_teapots, vflat, varray, center_teapots = scene_io_utils.loadTeapotsOpenDRData(renderTeapotsList, False, False, targetModels)

azimuth = np.pi
chCosAz = ch.Ch([np.cos(azimuth)])
chSinAz = ch.Ch([np.sin(azimuth)])

chAz = 2*ch.arctan(chSinAz/(ch.sqrt(chCosAz**2 + chSinAz**2) + chCosAz))
chAz = ch.Ch([0])
chObjAz = ch.Ch([0])
chAzRel = chAz - chObjAz

elevation = 0
chLogCosEl = ch.Ch(np.log(np.cos(elevation)))
chLogSinEl = ch.Ch(np.log(np.sin(elevation)))
chEl = 2*ch.arctan(ch.exp(chLogSinEl)/(ch.sqrt(ch.exp(chLogCosEl)**2 + ch.exp(chLogSinEl)**2) + ch.exp(chLogCosEl)))
chEl =  ch.Ch([0.95993109])
chDist = ch.Ch([camDistance])

chLightSHCoeffs = ch.Ch(np.array([2, 0.25, 0.25, 0.12,-0.17,0.36,0.1,0.,0.]))

clampedCosCoeffs = clampedCosineCoefficients()
chComponent = chLightSHCoeffs * clampedCosCoeffs

chPointLightIntensity = ch.Ch([1])

chLightAz = ch.Ch([0.0])
chLightEl = ch.Ch([np.pi/2])
chLightDist = ch.Ch([0.5])

light_color = ch.ones(3)*chPointLightIntensity

chVColors = ch.Ch([0.4,0.4,0.4])

chDisplacement = ch.Ch([0.0, 0.0,0.0])
chScale = ch.Ch([1.0,1.0,1.0])

# vcch[0] = np.ones_like(vcflat[0])*chVColorsGT.reshape([1,3])
renderer_teapots = []

for teapot_i in range(len(renderTeapotsList)):
    vmod = v_teapots[teapot_i]
    fmod_list = f_list_teapots[teapot_i]
    vcmod = vc_teapots[teapot_i]
    vnmod = vn_teapots[teapot_i]
    uvmod = uv_teapots[teapot_i]
    haveTexturesmod_list = haveTextures_list_teapots[teapot_i]
    texturesmod_list = textures_list_teapots[teapot_i]
    centermod = center_teapots[teapot_i]
    renderer = createRendererTarget(glMode, True, chAz, chObjAz, chEl, chDist, centermod, vmod, vcmod, fmod_list, vnmod, light_color, chComponent, chVColors, 0, chDisplacement, chScale, width,height, uvmod, haveTexturesmod_list, texturesmod_list, frustum, win )
    renderer.msaa = True
    renderer.r
    renderer_teapots = renderer_teapots + [renderer]

currentTeapotModel = 0

center = center_teapots[currentTeapotModel]

#########################################
# Initialization ends here
#########################################

#########################################
# Generative model set up
#########################################

rendererGT = ch.Ch(renderer.r.copy())
numPixels = width*height

E_raw = renderer - rendererGT
SE_raw = ch.sum(E_raw*E_raw, axis=2)

SSqE_raw = ch.SumOfSquares(E_raw)/numPixels

initialPixelStdev = 0.01
reduceVariance = False
# finalPixelStdev = 0.05
stds = ch.Ch([initialPixelStdev])
variances = stds ** 2
globalPrior = ch.Ch([0.9])

negLikModel = -ch.sum(generative_models.LogGaussianModel(renderer=renderer, groundtruth=rendererGT, variances=variances))
negLikModelRobust = -ch.sum(generative_models.LogRobustModel(renderer=renderer, groundtruth=rendererGT, foregroundPrior=globalPrior, variances=variances))
pixelLikelihoodCh = generative_models.LogGaussianModel(renderer=renderer, groundtruth=rendererGT, variances=variances)
pixelLikelihoodRobustCh = generative_models.LogRobustModel(renderer=renderer, groundtruth=rendererGT, foregroundPrior=globalPrior, variances=variances)
# negLikModel = -generative_models.modelLogLikelihoodCh(rendererGT, renderer, np.array([]), 'FULL', variances)/numPixels
# negLikModelRobust = -generative_models.modelLogLikelihoodRobustCh(rendererGT, renderer, np.array([]), 'FULL', globalPrior, variances)/numPixels
# pixelLikelihoodCh = generative_models.logPixelLikelihoodCh(rendererGT, renderer, np.array([]), 'FULL', variances)
# pixelLikelihoodRobustCh = ch.log(generative_models.pixelLikelihoodRobustCh(rendererGT, renderer, np.array([]), 'FULL', globalPrior, variances))

post = generative_models.layerPosteriorsRobustCh(rendererGT, renderer, np.array([]), 'FULL', globalPrior, variances)[0]

# modelLogLikelihoodRobustRegionCh = -ch.sum(generative_models.LogRobustModelRegion(renderer=renderer, groundtruth=rendererGT, foregroundPrior=globalPrior, variances=variances))/numPixels
#
# pixelLikelihoodRobustRegionCh = generative_models.LogRobustModelRegion(renderer=renderer, groundtruth=rendererGT, foregroundPrior=globalPrior, variances=variances)

import opendr.filters
robPyr = opendr.filters.gaussian_pyramid(renderer - rendererGT, n_levels=6, normalization='size')
robPyrSum = -ch.sum(ch.log(ch.exp(-0.5*robPyr**2/variances) + 1))

# models = [negLikModel, negLikModelRobust, hogError]
models = [negLikModel, negLikModelRobust, robPyrSum]
pixelModels = [pixelLikelihoodCh, pixelLikelihoodRobustCh, robPyr]
modelsDescr = ["Gaussian Model", "Outlier model", "Region Robust" ]

model = 1
pixelErrorFun = pixelModels[model]
errorFun = models[model]
iterat = 0

t = time.time()

def cb(_):
    global t
    global samplingMode
    elapsed_time = time.time() - t
    print("Ended interation in  " + str(elapsed_time))
    # if samplingMode:
    #     analyzeAz(resultDir + 'az_samples/test' + str(test_i) +'/azNum' + str(sampleAzNum) + '_it' + str(iterat)  , rendererGT, renderer, chEl.r, chVColors.r, chLightSHCoeffs.r, azsPredictions[test_i], sampleStds=stds.r)
    # else:
    #     analyzeAz(resultDir + 'az_samples/test' + str(test_i) +'/min_azNum' + str(sampleAzNum) +  '_it' + str(iterat)  , rendererGT, renderer, chEl.r, chVColors.r, chLightSHCoeffs.r, azsPredictions[test_i], sampleStds=stds.r)
    global pixelErrorFun
    global errorFun
    global iterat
    iterat = iterat + 1
    print("Callback! " + str(iterat))
    print("Sq Error: " + str(errorFun.r))

    global negLikModelRobustSmallStd
    global bestShapeParamsSmallStd
    global bestRobustSmallStdError
    if minimizingShape and useShapeModel:
        # if negLikModelRobustSmallStd.r  < bestRobustSmallStdError:
        #     bestRobustSmallStdError = negLikModelRobustSmallStd.r.copy()
        #     bestShapeParamsSmallStd = chShapeParams.r.copy()
        maxShapeSize = 2.5
        largeShapeParams = np.abs(chShapeParams.r) > maxShapeSize
        if np.any(largeShapeParams):
            print("Warning: found large shape parameters to fix!")
        chShapeParams[largeShapeParams] = np.sign(chShapeParams.r[largeShapeParams])*maxShapeSize

    print("Small Std Error " + str(negLikModelRobustSmallStd.r))
    global imagegt
    global renderer
    global gradAz
    global gradEl
    global performance
    global azimuths
    global elevations
    global shapeParams

    t = time.time()

#########################################
# Generative model setup ends here.
#########################################

#########################################
# Test code starts here:
#########################################


gtDir = 'groundtruth/' + gtPrefix + '/'
featuresDir = gtDir

experimentDir = 'experiments/' + experimentPrefix + '/'
trainModelsDirPose = 'experiments/' + trainPrefixPose + '/'
trainModelsDirVColor = 'experiments/' + trainPrefixVColor + '/'
trainModelsDirLightCoeffs = 'experiments/' + trainPrefixLightCoeffs + '/'
trainModelsDirShapeParams = 'experiments/' + trainPrefixShapeParams + '/'
trainModelsDirAppLight = 'experiments/' + trainModelsDirAppLight + '/'

useShapeModel = True

ignoreGT = True
ignore = []
if os.path.isfile(gtDir + 'ignore.npy'):
    ignore = np.load(gtDir + 'ignore.npy')

groundTruthFilename = gtDir + 'groundTruth.h5'
gtDataFile = h5py.File(groundTruthFilename, 'r')

rangeTests = [[4,49,75,72,15,43, 88]]
rangeTests = [[4,49,75, 72]]
rangeTests = np.arange(100,1100)
rangeTests = np.arange(2)
# rangeTests = np.arange(2)
# testSet = np.load(experimentDir + 'test.npy')[:numTests][[10,19,20,23,25,39,4,49,63,8,80]]
# testSet = np.load(experimentDir + 'test.npy')[:numTests][[19,23,25,4,8]]

testSet = np.load(experimentDir + 'test.npy')[rangeTests]

numTests = len(testSet)
# testSet = np.load(experimentDir + 'test.npy')[:numTests][[49]]
# testSet = np.load(experimentDir + 'test.npy')[:numTests][[75]]
# testSet = np.load(experimentDir + 'test.npy')[:numTests][[4,49]]
# testSet = np.load(experimentDir + 'test.npy')[:numTests]
# testSet = np.load(experimentDir + 'test.npy')[[ 3,  5, 14, 21, 35, 36, 54, 56, 59, 60, 68, 70, 72, 79, 83, 85, 89,94]]
# [13:14]

#Bad samples for data set train5 out normal.
# testSet = np.array([162371, 410278, 132297, 350815, 104618, 330181,  85295,  95047,
#        410233, 393785, 228626, 452094, 117242,  69433,  35352,  31030,
#        268444, 147111, 117287, 268145, 478618, 334784])

shapeGT = gtDataFile[gtPrefix].shape
boolTestSet = np.zeros(shapeGT).astype(np.bool)
boolTestSet[testSet] = True
testGroundTruth = gtDataFile[gtPrefix][boolTestSet]
groundTruthTest = np.zeros(shapeGT, dtype=testGroundTruth.dtype)
groundTruthTest[boolTestSet] = testGroundTruth
groundTruth = groundTruthTest[testSet]
dataTeapotIdsTest = groundTruth['trainTeapotIds']
test = np.arange(len(testSet))

# testSamplesIds= [2]
# test = np.array([],dtype=np.uint16)
# for testId in testSamplesIds:
#     test = np.append(test, np.where(dataTeapotIdsTest == testId))
#
# groundTruth = groundTruth[test]
#

testSet = testSet[test]

print("Reading experiment.")
dataAzsGT = groundTruth['trainAzsGT']
dataObjAzsGT = groundTruth['trainObjAzsGT']
dataElevsGT = groundTruth['trainElevsGT']
dataLightAzsGT = groundTruth['trainLightAzsGT']
dataLightElevsGT = groundTruth['trainLightElevsGT']
dataLightIntensitiesGT = groundTruth['trainLightIntensitiesGT']
dataVColorGT = groundTruth['trainVColorGT']
dataScenes = groundTruth['trainScenes']
dataTeapotIds = groundTruth['trainTeapotIds']
dataEnvMaps = groundTruth['trainEnvMaps']
dataOcclusions = groundTruth['trainOcclusions']
dataTargetIndices = groundTruth['trainTargetIndices']
dataLightCoefficientsGT = groundTruth['trainLightCoefficientsGT']
dataLightCoefficientsGTRel = groundTruth['trainLightCoefficientsGTRel']
dataAmbientIntensityGT = groundTruth['trainAmbientIntensityGT']
dataIds = groundTruth['trainIds']

if useShapeModel:
    dataShapeModelCoeffsGT = groundTruth['trainShapeModelCoeffsGT']

gtDtype = groundTruth.dtype

# testSet = np.array([ 11230, 3235, 10711,  9775, 11230, 10255,  5060, 12784,  5410,  1341,14448, 12935, 13196,  6728,  9002,  7946,  1119,  5827,  4842,12435,  8152,  4745,  9512,  9641,  7165, 13950,  3567,   860,4105, 10330,  7218, 10176,  2310,  5325])

testSetFixed = testSet
whereBad = []
for test_it, test_id in enumerate(testSet):
    if test_id in ignore:
        bad = np.where(testSetFixed==test_id)
        testSetFixed = np.delete(testSetFixed, bad)
        whereBad = whereBad + [bad]

# testSet = testSetFixed

loadFromHdf5 = False

syntheticGroundtruth = True

synthPrefix = '_cycles'
if syntheticGroundtruth:
    synthPrefix = ''

if syntheticGroundtruth:
    imagesDir = gtDir + 'images_opendr/'
else:
    imagesDir = gtDir + 'images/'
images = readImages(imagesDir, dataIds, loadFromHdf5)

print("Backprojecting and fitting estimates.")
# testSet = np.arange(len(images))[0:10]

testAzsGT = dataAzsGT
testObjAzsGT = dataObjAzsGT
testElevsGT = dataElevsGT
testLightAzsGT = dataLightAzsGT
testLightElevsGT = dataLightElevsGT
testLightIntensitiesGT = dataLightIntensitiesGT
testVColorGT = dataVColorGT
if useShapeModel:
    testShapeParamsGT = dataShapeModelCoeffsGT

testLightCoefficientsGTRel = dataLightCoefficientsGTRel * dataAmbientIntensityGT[:,None]

testAzsRel = np.mod(testAzsGT - testObjAzsGT, 2*np.pi)


##Read Training set labels

trainSet = np.load(experimentDir + 'train.npy')

shapeGT = gtDataFile[gtPrefix].shape
boolTrainSet = np.zeros(shapeGT).astype(np.bool)
boolTrainSet[trainSet] = True
trainGroundTruth = gtDataFile[gtPrefix][boolTrainSet]
groundTruthTrain = np.zeros(shapeGT, dtype=trainGroundTruth.dtype)
groundTruthTrain[boolTrainSet] = trainGroundTruth
groundTruthTrain = groundTruthTrain[trainSet]
dataTeapotIdsTrain = groundTruthTrain['trainTeapotIds']
train = np.arange(len(trainSet))

testSet = testSet[test]

print("Reading experiment.")
trainAzsGT = groundTruthTrain['trainAzsGT']
trainObjAzsGT = groundTruthTrain['trainObjAzsGT']
trainElevsGT = groundTruthTrain['trainElevsGT']
trainLightAzsGT = groundTruthTrain['trainLightAzsGT']
trainLightElevsGT = groundTruthTrain['trainLightElevsGT']
trainLightIntensitiesGT = groundTruthTrain['trainLightIntensitiesGT']
trainVColorGT = groundTruthTrain['trainVColorGT']
trainScenes = groundTruthTrain['trainScenes']
trainTeapotIds = groundTruthTrain['trainTeapotIds']
trainEnvMaps = groundTruthTrain['trainEnvMaps']
trainOcclusions = groundTruthTrain['trainOcclusions']
trainTargetIndices = groundTruthTrain['trainTargetIndices']
trainLightCoefficientsGT = groundTruthTrain['trainLightCoefficientsGT']
trainLightCoefficientsGTRel = groundTruthTrain['trainLightCoefficientsGTRel']
trainAmbientIntensityGT = groundTruthTrain['trainAmbientIntensityGT']
trainIds = groundTruthTrain['trainIds']

if useShapeModel:
    trainShapeModelCoeffsGT = groundTruthTrain['trainShapeModelCoeffsGT']

trainLightCoefficientsGTRel = trainLightCoefficientsGTRel * trainAmbientIntensityGT[:,None]

trainAzsRel = np.mod(trainAzsGT - trainObjAzsGT, 2*np.pi)


recognitionTypeDescr = ["near", "mean", "sampling"]
recognitionType = 1

optimizationTypeDescr = ["predict", "optimize", "joint"]
optimizationType = 0
computePredErrorFuns = True

method = 1
model = 1
maxiter = 100
numSamples = 1

free_variables = [ chAz, chEl, chVColors, chLightSHCoeffs]

mintime = time.time()
boundEl = (-np.pi, np.pi)
boundAz = (-3*np.pi, 3*np.pi)
boundscomponents = (0,None)
bounds = [boundAz,boundEl]
bounds = [(None , None ) for sublist in free_variables for item in sublist]
methods = ['dogleg', 'minimize', 'BFGS', 'L-BFGS-B', 'Nelder-Mead', 'SGDMom', 'probLineSearch']
options = {'disp':False, 'maxiter':maxiter, 'lr':0.0001, 'momentum':0.1, 'decay':0.99}
azVar = 0.1
elVar = 0.1
vColorVar = 0.01
shCoeffsVar = 0.01
df_vars = np.concatenate([azVar*np.ones(chAz.shape), elVar*np.ones(chEl.shape), vColorVar*np.ones(chVColors.r.shape), shCoeffsVar*np.ones(chLightSHCoeffs.r.shape)])
options = {'disp':False, 'maxiter':maxiter, 'df_vars':df_vars}


testRenderer = 0

# testRenderer = 2
if useShapeModel:
    import shape_model
    #%% Load data
    filePath = 'data/teapotModel.pkl'
    teapotModel = shape_model.loadObject(filePath)
    faces = teapotModel['faces']

    #%% Sample random shape Params
    latentDim = np.shape(teapotModel['ppcaW'])[1]
    shapeParams = np.random.randn(latentDim)
    chShapeParams = ch.Ch(shapeParams)

    meshLinearTransform=teapotModel['meshLinearTransform']
    W=teapotModel['ppcaW']
    b=teapotModel['ppcaB']

    chVertices = shape_model.VerticesModel(chShapeParams=chShapeParams,meshLinearTransform=meshLinearTransform,W = W,b=b)
    chVertices.init()

    chVertices = ch.dot(geometry.RotateZ(-np.pi/2)[0:3,0:3],chVertices.T).T

    chNormals = shape_model.chGetNormals(chVertices, faces)

    smNormals = [chNormals]
    smFaces = [[faces]]
    smVColors = [chVColors*np.ones(chVertices.shape)]
    smUVs = ch.Ch(np.zeros([chVertices.shape[0],2]))
    smHaveTextures = [[False]]
    smTexturesList = [[None]]

    chVertices = chVertices - ch.mean(chVertices, axis=0)
    minZ = ch.min(chVertices[:,2])

    chMinZ = ch.min(chVertices[:,2])

    zeroZVerts = chVertices[:,2]- chMinZ
    chVertices = ch.hstack([chVertices[:,0:2] , zeroZVerts.reshape([-1,1])])

    chVertices = chVertices*0.09
    smCenter = ch.array([0,0,0.1])

    smVertices = [chVertices]
    chNormals = shape_model.chGetNormals(chVertices, faces)
    smNormals = [chNormals]

    renderer = createRendererTarget(glMode, True, chAz, chObjAz, chEl, chDist, smCenter, [smVertices], [smVColors], [smFaces], [smNormals], light_color, chComponent, chVColors, 0, chDisplacement, chScale, width,height, [smUVs], [smHaveTextures], [smTexturesList], frustum, win )
    renderer.msaa = True
    renderer.overdraw = True

else:
    renderer = renderer_teapots[testRenderer]

nearGTOffsetRelAz = 0
nearGTOffsetEl = 0
nearGTOffsetLighCoeffs = np.zeros(9)
nearGTOffsetVColor = np.zeros(3)

############ RECOGNITION MDOEL PREDICTIONS (COMPUTE AND SAVE, DON'T USE THIS EVERY TIME)

#Load trained recognition models
nnBatchSize = 100

azsPredictions = np.array([])

recomputeMeans = False
includeMeanBaseline = True

recomputePredictions = False

if includeMeanBaseline:
    meanTrainLightCoefficientsGTRel = np.repeat(np.mean(trainLightCoefficientsGTRel, axis=0)[None,:], numTests, axis=0)
    meanTrainElevation = np.repeat(np.mean(trainElevsGT, axis=0), numTests,  axis=0)
    meanTrainAzimuthRel = np.repeat(0, numTests, axis=0)
    meanTrainShapeParams = np.repeat(np.zeros([latentDim])[None,:], numTests, axis=0)
    meanTrainVColors = np.repeat(np.mean(trainVColorGT, axis=0)[None,:], numTests, axis=0)
    chShapeParams[:] = np.zeros([10])
    meanTrainShapeVertices = np.repeat(chVertices.r.copy()[None,:], numTests, axis=0)

    if recomputeMeans or not os.path.isfile(experimentDir + "meanTrainEnvMapProjections.npy"):
        envMapTexture = np.zeros([180,360,3])
        approxProjectionsPredList = []
        for train_i in range(len(trainSet)):
            pEnvMap = SHProjection(envMapTexture, np.concatenate([trainLightCoefficientsGTRel[train_i][:,None], trainLightCoefficientsGTRel[train_i][:,None], trainLightCoefficientsGTRel[train_i][:,None]], axis=1))
            approxProjectionPred = np.sum(pEnvMap, axis=(2,3))

            approxProjectionsPredList = approxProjectionsPredList + [approxProjectionPred[None,:]]
        approxProjections = np.vstack(approxProjectionsPredList)
        meanTrainEnvMapProjections = np.mean(approxProjections, axis=0)
        np.save(experimentDir + 'meanTrainEnvMapProjections.npy', meanTrainEnvMapProjections)
    else:
        meanTrainEnvMapProjections = np.load(experimentDir + 'meanTrainEnvMapProjections.npy')

    meanTrainEnvMapProjections = np.repeat(meanTrainEnvMapProjections[None,:], numTests, axis=0)

if recomputePredictions or not os.path.isfile(trainModelsDirPose + "elevsPred.npy"):
    if 'neuralNetPose' in parameterRecognitionModels:
        import theano
        # theano.sandbox.cuda.use('cpu')
        import lasagne
        import lasagne_nn

        poseModel = ""
        with open(trainModelsDirPose + 'neuralNetModelPose.pickle', 'rb') as pfile:
            neuralNetModelPose = pickle.load(pfile)

        meanImage = neuralNetModelPose['mean']
        modelType = neuralNetModelPose['type']
        param_values = neuralNetModelPose['params']
        grayTestImages =  0.3*images[:,:,:,0] +  0.59*images[:,:,:,1] + 0.11*images[:,:,:,2]
        grayTestImages = grayTestImages[:,None, :,:]

        grayTestImages = grayTestImages - meanImage.reshape([1,1, grayTestImages.shape[2],grayTestImages.shape[3]])

        network = lasagne_nn.load_network(modelType=modelType, param_values=param_values)
        posePredictionFun = lasagne_nn.get_prediction_fun(network)

        posePredictions = np.zeros([len(grayTestImages), 4])
        for start_idx in range(0, len(grayTestImages), nnBatchSize):
            posePredictions[start_idx:start_idx + nnBatchSize] = posePredictionFun(grayTestImages.astype(np.float32)[start_idx:start_idx + nnBatchSize])
        # posePredictions = posePredictionFun(grayTestImages.astype(np.float32))

        cosAzsPred = posePredictions[:,0]
        sinAzsPred = posePredictions[:,1]
        cosElevsPred = posePredictions[:,2]
        sinElevsPred = posePredictions[:,3]


        elevsPred = np.arctan2(sinElevsPred, cosElevsPred)
        azsPred = np.arctan2(sinAzsPred, cosAzsPred)

        np.save(trainModelsDirPose + 'elevsPred.npy', elevsPred)
        np.save(trainModelsDirPose + 'azsPred.npy', azsPred)

        # ##Get predictions with dropout on to get samples.
        # with open(trainModelsDirPose + 'neuralNetModelPose.pickle', 'rb') as pfile:
        #     neuralNetModelPose = pickle.load(pfile)
        #
        # meanImage = neuralNetModelPose['mean']
        # modelType = neuralNetModelPose['type']
        # param_values = neuralNetModelPose['params']
        # grayTestImages =  0.3*images[:,:,:,0] +  0.59*images[:,:,:,1] + 0.11*images[:,:,:,2]
        # grayTestImages = grayTestImages[:,None, :,:]
        # grayTestImages = grayTestImages - meanImage.reshape([1,1, grayTestImages.shape[2],grayTestImages.shape[3]])
        #
        # # network = lasagne_nn.load_network(modelType=modelType, param_values=param_values)
        # nonDetPosePredictionFun = lasagne_nn.get_prediction_fun_nondeterministic(network)
        # posePredictionsSamples = []
        # cosAzsPredSamples = []
        # sinAzsPredSamples = []
        # for i in range(100):
        #     posePredictionsSample = np.zeros([len(grayTestImages), 4])
        #     for start_idx in range(0, len(grayTestImages), nnBatchSize):
        #         posePredictionsSample[start_idx:start_idx + nnBatchSize] = nonDetPosePredictionFun(grayTestImages.astype(np.float32)[start_idx:start_idx + nnBatchSize])
        #
        #     cosAzsPredSample = posePredictionsSample[:,0]
        #     sinAzsPredSample = posePredictionsSample[:,1]
        #     cosAzsPredSamples = cosAzsPredSamples + [cosAzsPredSample[:,None]]
        #     sinAzsPredSamples = sinAzsPredSamples + [sinAzsPredSample[:,None]]
        #
        # cosAzsPredSamples = np.hstack(cosAzsPredSamples)
        # sinAzsPredSamples = np.hstack(sinAzsPredSamples)
        #
        # azsPredictions = np.arctan2(sinAzsPredSamples, cosAzsPredSamples)

else:
    elevsPred = np.load(trainModelsDirPose + 'elevsPred.npy')[rangeTests]
    azsPred = np.load(trainModelsDirPose + 'azsPred.npy')[rangeTests]


if recomputePredictions or not os.path.isfile(trainModelsDirVColor + "vColorsPred.npy"):

    if 'neuralNetVColors' in parameterRecognitionModels:

        import theano
        # theano.sandbox.cuda.use('cpu')
        import lasagne
        import lasagne_nn

        nnModel = ""
        with open(trainModelsDirVColor + 'neuralNetModelAppearance.pickle', 'rb') as pfile:
            neuralNetModelAppearance = pickle.load(pfile)

        meanImage = neuralNetModelAppearance['mean']
        modelType = neuralNetModelAppearance['type']
        param_values = neuralNetModelAppearance['params']

        testImages = images.reshape([images.shape[0],3,images.shape[1],images.shape[2]]) - meanImage.reshape([1,meanImage.shape[2], meanImage.shape[0],meanImage.shape[1]]).astype(np.float32)

        network = lasagne_nn.load_network(modelType=modelType, param_values=param_values)
        appPredictionFun = lasagne_nn.get_prediction_fun(network)

        appPredictions = np.zeros([len(testSet), 3])
        for start_idx in range(0, len(testSet), nnBatchSize):
            appPredictions[start_idx:start_idx + nnBatchSize] = appPredictionFun(testImages.astype(np.float32)[start_idx:start_idx + nnBatchSize])

        vColorsPred = appPredictions

        np.save(trainModelsDirPose + 'vColorsPred.npy', vColorsPred)

        #Samples:
        # vColorsPredSamples = []
        # appPredictionNonDetFun = lasagne_nn.get_prediction_fun_nondeterministic(network)
        #
        # for i in range(100):
        #     appPredictionsSample = np.zeros([len(testImages), 3])
        #     for start_idx in range(0, len(testImages), nnBatchSize):
        #         appPredictionsSample[start_idx:start_idx + nnBatchSize] = appPredictionNonDetFun(testImages.astype(np.float32)[start_idx:start_idx + nnBatchSize])
        #
        #     vColorsPredSamples = vColorsPredSamples + [appPredictionsSample[:,:][:,:,None]]
        #
        # vColorsPredSamples = np.concatenate(vColorsPredSamples, axis=2)

    if 'randForestVColors' in parameterRecognitionModels:
        with open(trainModelsDirVColor + 'randForestModelVColor.pickle', 'rb') as pfile:
            randForestModelVColor = pickle.load(pfile)

        colorWindow = 30
        image = images[0]
        croppedImages = images[:,image.shape[0]/2-colorWindow:image.shape[0]/2+colorWindow,image.shape[1]/2-colorWindow:image.shape[1]/2+colorWindow,:]
        vColorsPred = recognition_models.testRandomForest(randForestModelVColor, croppedImages.reshape([len(testSet),-1]))

    if 'linearRegressionVColors' in parameterRecognitionModels:
        with open(trainModelsDirVColor + 'linearRegressionModelVColor.pickle', 'rb') as pfile:
            linearRegressionModelVColor = pickle.load(pfile)

        colorWindow = 30
        image = images[0]
        croppedImages = images[:,image.shape[0]/2-colorWindow:image.shape[0]/2+colorWindow,image.shape[1]/2-colorWindow:image.shape[1]/2+colorWindow,:]
        vColorsPred = recognition_models.testLinearRegression(linearRegressionModelVColor, croppedImages.reshape([len(testSet),-1]))

    if 'medianVColors' in parameterRecognitionModels:
        # recognition_models.medianColor(image, win)
        colorWindow = 30
        imagesWin = images[:,images.shape[1]/2-colorWindow:images.shape[1]/2+colorWindow,images.shape[2]/2-colorWindow:images.shape[2]/2+colorWindow,:]
        vColorsPred = np.median(imagesWin.reshape([images.shape[0],-1,3]), axis=1)/1.4
        # return color
else:
    vColorsPred = np.load(trainModelsDirVColor + 'vColorsPred.npy')[rangeTests]

SHModel = ""

# import theano
# import theano.tensor as T

# ## Theano NN error function 1.
# with open(trainModelsDirPose + 'neuralNetModelPose.pickle', 'rb') as pfile:
#     neuralNetModelPose = pickle.load(pfile)
#
# meanImage = neuralNetModelPose['mean'].reshape([150,150])
#
# modelType = neuralNetModelPose['type']
# param_values = neuralNetModelPose['params']
# network = lasagne_nn.load_network(modelType=modelType, param_values=param_values)
# layer = lasagne.layers.get_all_layers(network)[-2]
# inputLayer = lasagne.layers.get_all_layers(network)[0]
# layer_output = lasagne.layers.get_output(layer, deterministic=True)
# dim_output= layer.output_shape[1]
#
# networkGT = lasagne_nn.load_network(modelType=modelType, param_values=param_values)
# layerGT = lasagne.layers.get_all_layers(networkGT)[-2]
# inputLayerGT = lasagne.layers.get_all_layers(networkGT)[0]
# layer_outputGT = lasagne.layers.get_output(layerGT, deterministic=True)
#
# rendererGray =  0.3*renderer[:,:,0] +  0.59*renderer[:,:,1] + 0.11*renderer[:,:,2]
# rendererGrayGT =  0.3*rendererGT[:,:,0] +  0.59*rendererGT[:,:,1] + 0.11*rendererGT[:,:,2]
#
# chThError = TheanoFunOnOpenDR(theano_input=inputLayer.input_var, theano_output=layer_output, opendr_input=rendererGray - meanImage, dim_output = dim_output,
#                               theano_input_gt=inputLayerGT.input_var, theano_output_gt=layer_outputGT, opendr_input_gt=rendererGrayGT - meanImage)
#
# chThError.compileFunctions(layer_output, theano_input=inputLayer.input_var, dim_output=dim_output, theano_input_gt=inputLayerGT.input_var, theano_output_gt=layer_outputGT)
#
# chThError.r

if recomputePredictions or not os.path.isfile(trainModelsDirLightCoeffs + "relLightCoefficientsPred.npy"):
    if 'neuralNetModelSHLight' in parameterRecognitionModels:

        import theano
        # theano.sandbox.cuda.use('cpu')
        import lasagne
        import lasagne_nn


        nnModel = ""
        with open(trainModelsDirLightCoeffs + 'neuralNetModelLight.pickle', 'rb') as pfile:
            neuralNetModelSHLight = pickle.load(pfile)

        meanImage = neuralNetModelSHLight['mean']
        modelType = neuralNetModelSHLight['type']
        param_values = neuralNetModelSHLight['params']

        testImages = images.reshape([images.shape[0],3,images.shape[1],images.shape[2]]) - meanImage.reshape([1,meanImage.shape[2], meanImage.shape[0],meanImage.shape[1]]).astype(np.float32)

        network = lasagne_nn.load_network(modelType=modelType, param_values=param_values)
        lightPredictionFun = lasagne_nn.get_prediction_fun(network)

        lightPredictions = np.zeros([len(testImages), 9])
        for start_idx in range(0, len(testImages), nnBatchSize):
            lightPredictions[start_idx:start_idx + nnBatchSize] = lightPredictionFun(testImages.astype(np.float32)[start_idx:start_idx + nnBatchSize])

        relLightCoefficientsPred = lightPredictions

        np.save(trainModelsDirLightCoeffs + 'relLightCoefficientsPred.npy', relLightCoefficientsPred)


else:
    relLightCoefficientsPred = np.load(trainModelsDirLightCoeffs + 'relLightCoefficientsPred.npy')[rangeTests]

if recomputePredictions or not os.path.isfile(trainModelsDirShapeParams + "shapeParamsPred.npy"):
    if 'neuralNetModelShape' in parameterRecognitionModels and useShapeModel:

        import theano
        # theano.sandbox.cuda.use('cpu')
        import lasagne
        import lasagne_nn

        nnModel = ""
        with open(trainModelsDirShapeParams + 'neuralNetModelShape.pickle', 'rb') as pfile:
            neuralNetModelSHLight = pickle.load(pfile)

        meanImage = neuralNetModelSHLight['mean']
        modelType = neuralNetModelSHLight['type']
        param_values = neuralNetModelSHLight['params']

        grayTestImages =  0.3*images[:,:,:,0] +  0.59*images[:,:,:,1] + 0.11*images[:,:,:,2]
        grayTestImages = grayTestImages[:,None, :,:]
        grayTestImages = grayTestImages - meanImage.reshape([1,1, grayTestImages.shape[2],grayTestImages.shape[3]])

        network = lasagne_nn.load_network(modelType=modelType, param_values=param_values)
        shapePredictionFun = lasagne_nn.get_prediction_fun(network)

        shapePredictions = np.zeros([len(grayTestImages), latentDim])
        for start_idx in range(0, len(testImages), nnBatchSize):
            shapePredictions[start_idx:start_idx + nnBatchSize] = shapePredictionFun(grayTestImages.astype(np.float32)[start_idx:start_idx + nnBatchSize])

        shapeParamsPred = shapePredictions

        np.save(trainModelsDirShapeParams + 'shapeParamsPred.npy', shapeParamsPred)
else:
    shapeParamsPred = np.load(trainModelsDirShapeParams + 'shapeParamsPred.npy')[rangeTests]


if recomputePredictions or not os.path.isfile(trainModelsDirShapeParams + "neuralNetModelMaskLarge.npy"):
    if 'neuralNetModelMask' in parameterRecognitionModels:

        import theano
        # theano.sandbox.cuda.use('cpu')
        import lasagne
        import lasagne_nn


        nnModel = ""
        with open(trainModelsDirLightCoeffs + 'neuralNetModelMaskLarge.pickle', 'rb') as pfile:
            neuralNetModelSHLight = pickle.load(pfile)

        meanImage = neuralNetModelSHLight['mean']
        modelType = neuralNetModelSHLight['type']
        param_values = neuralNetModelSHLight['params']

        testImages = images.reshape([images.shape[0],3,images.shape[1],images.shape[2]]) - meanImage.reshape([1,meanImage.shape[2], meanImage.shape[0],meanImage.shape[1]]).astype(np.float32)

        network = lasagne_nn.load_network(modelType=modelType, param_values=param_values)
        maskPredictionFun = lasagne_nn.get_prediction_fun(network)

        maskPredictions = np.zeros([len(testImages), 50*50])
        for start_idx in range(0, len(testImages), nnBatchSize):
            maskPredictions[start_idx:start_idx + nnBatchSize] = maskPredictionFun(testImages.astype(np.float32)[start_idx:start_idx + nnBatchSize])

        maskPredictions = np.reshape(maskPredictions, [len(testImages), 50,50])

        np.save(trainModelsDirShapeParams + 'maskPredictions.npy', maskPredictions)

        # # #Samples:
        # maskSamples = []
        # maskPredNonDetFun = lasagne_nn.get_prediction_fun_nondeterministic(network)
        #
        # for i in range(100):
        #     maskPredictionsSamples = np.zeros([len(testImages), 50*50])
        #     for start_idx in range(0, len(testImages),nnBatchSize):
        #         maskPredictionsSamples[start_idx:start_idx + nnBatchSize] = maskPredNonDetFun(testImages.astype(np.float32)[start_idx:start_idx + nnBatchSize])
        #
        #     maskSamples = maskSamples + [maskPredictionsSamples[:,:][:,:,None]]
        #
        # maskSamples = np.concatenate(maskSamples, axis=2)
        # loadMask = True
        #
        # gtDirMask = 'groundtruth/train4_occlusion_mask/'
        #
        # masksDir =  gtDirMask + 'masks_occlusion/'
        # if loadMask:
        #     masksGT = loadMasks(masksDir, testSet)
else:
    maskPredictions = np.load(trainModelsDirShapeParams + 'maskPredictions.npy')[rangeTests]


loadMask = True
if loadMask:
    masksGT = loadMasks(gtDir + '/masks_occlusion/', testSet)

print("Finished loading and compiling recognition models")


envMapDic = {}
SHFilename = 'data/LightSHCoefficients.pickle'

with open(SHFilename, 'rb') as pfile:
    envMapDic = pickle.load(pfile)
hdritems = list(envMapDic.items())[:]

## NN prediction samples analysis.
# directory = resultDir
# plt.ioff()
# fig = plt.figure()
# errorFun = models[0]
# for test_i, sampleAzsPredictions in enumerate(azsPredictions):
#
#     testId = dataIds[test_i]
#
#     rendererGT[:] = srgb2lin(images[test_i])
#
#     testnum = (test_i + 1)*2
#
#     plt.scatter(np.ones_like(sampleAzsPredictions)*testnum, np.mod(sampleAzsPredictions*180/np.pi, 360), c='b')
#
#     bestAzErr = np.finfo('f').max
#     bestAz = testAzsRel[test_i]
#     bestAzNormalErr = np.finfo('f').max
#     bestAzNormal = testAzsRel[test_i]
#     for sample_i in range(len(testAzsRel)):
#
#         color = testVColorGT[test_i]
#         az =  sampleAzsPredictions[sample_i]
#         el = testElevsGT[test_i]
#         lightCoefficientsRel = testLightCoefficientsGTRel[test_i]
#         chAz[:] = az
#         chEl[:] = el
#         chVColors[:] = color
#         chLightSHCoeffs[:] = lightCoefficientsRel
#         if chThError.r < bestAzErr:
#             bestAzErr = chThError.r
#             bestAz = az
#         if errorFun.r < bestAzNormalErr:
#             bestAzNormalErr = errorFun.r
#             bestAzNormal = az
#
#     from sklearn import mixture
#     # gmm = mixture.GMM(n_components=20, covariance_type='spherical', min_covar=radians(5)**2, init_params='wmc', params='wmc')
#
#     # gmm.fit(np.hstack([sinAzsPredictions[:,sample_i][:,None], cosAzsPredictions[:,sample_i][:,None]]))
#     # azsGmms = azsGmms + [gmm]
#     # for comp_i, weight in enumerate(gmm.weights_):
#     #     meanSin = gmm.means_[comp_i][0]
#     #     meanCos = gmm.means_[comp_i][1]
#     #     azCompMean = np.arctan2(meanSin, meanCos)
#     #     plt.plot(sample-0.4, np.mod(azCompMean*180/np.pi, 360), marker='o', ms=weight*50, c='y')
#     plt.plot(testnum,np.mod(bestAzNormal*180/np.pi,360), marker='o', ms=20, c='purple')
#     plt.plot(testnum,np.mod(bestAz*180/np.pi,360), marker='o', ms=20, c='y')
#     plt.plot(testnum,testAzsRel[test_i]*180/np.pi, marker='o', ms=20, c='g')
#     plt.plot(testnum, np.mod(azsPred[test_i]*180/np.pi, 360), marker='o', ms=20, c='r')
#
# plt.xlabel('Sample')
# plt.ylabel('Angular error')
# x1,x2,y1,y2 = plt.axis()
# plt.axis((0,len(testSet+1)*2,0,360))
# plt.title('Neuralnet multiple predictions')
# fig.savefig(directory + 'neuralNet_Az_scatter.png', bbox_inches='tight')
# plt.close(fig)
# # elsPredictions = [np.arctan2(sinElsPredictions[i], cosAzsPredictions[i]) for i in range(len(cosAzsPredictions))]
#
#

analyzeSamples = False

def analyzeHue(figurePath, rendererGT, renderer, sampleEl, sampleAz, sampleSH, sampleVColorsPredictions=None, sampleStds=0.1):
    global stds
    global chAz
    global test_i
    global samplingMode

    plt.ioff()
    fig = plt.figure()

    stds[:] = sampleStds
    negLikModel = -ch.sum(generative_models.LogGaussianModel(renderer=renderer, groundtruth=rendererGT, variances=variances))
    negLikModelRobust = -ch.sum(generative_models.LogRobustModel(renderer=renderer, groundtruth=rendererGT, foregroundPrior=globalPrior, variances=variances))
    stds = ch.Ch([initialPixelStdev])

    models = [negLikModel, negLikModelRobust, negLikModelRobust]
    errorFunRobust = models[1]
    errorFunGaussian = models[0]

    vColorsPredSamplesHSV = cv2.cvtColor(np.uint8(sampleVColorsPredictions.reshape([1, 100, 3])*255), cv2.COLOR_RGB2HSV)[0,:,0]

    plt.hist(vColorsPredSamplesHSV, bins=30, alpha=0.2)

    hueGT = cv2.cvtColor(np.uint8(testVColorGT[test_i][None,None,:]*255), cv2.COLOR_RGB2HSV)[0,0,0]
    huePred = cv2.cvtColor(np.uint8(vColorsPred[test_i][None,None,:]*255), cv2.COLOR_RGB2HSV)[0,0,0]

    chAz[:] = sampleAz
    chEl[:] = sampleEl
    currentVColors = chVColors.r
    currentHSV = cv2.cvtColor(np.uint8(currentVColors[None,None,:]*255), cv2.COLOR_RGB2HSV)[0,0]

    chLightSHCoeffs[:] = sampleSH

    trainingTeapots = [0]
    hueRange = np.arange(0,255,5)
    # chThErrors = np.zeros([len(trainingTeapots), len(hueRange)])

    robustErrors = np.array([])
    gaussianErrors = np.array([])
    hues = np.array([])
    for hue_i, hue in enumerate(hueRange):
        hues = np.append(hues, hue)

        color = cv2.cvtColor(np.array([hue, currentHSV[1],currentHSV[2]])[None,None,:].astype(np.uint8), cv2.COLOR_HSV2RGB)/255
        chVColors[:] = color

        for idx, renderer_idx in enumerate(trainingTeapots):
            renderer_i = renderer_teapots[renderer_idx]
            rendererGray =  0.3*renderer_i[:,:,0] +  0.59*renderer_i[:,:,1] + 0.11*renderer_i[:,:,2]
            # chThError.opendr_input = rendererGray
            # chThErrors[idx, az_i] = chThError.r

        robustErrors = np.append(robustErrors, errorFunRobust.r)
        gaussianErrors = np.append(gaussianErrors, errorFunGaussian.r)

    x1,x2,y1,y2 = plt.axis()

    robustErrors = robustErrors - np.min(robustErrors)
    gaussianErrors = gaussianErrors - np.min(gaussianErrors)
    # chThErrors = chThErrors - np.min(chThErrors)
    plt.plot(hues, robustErrors*y2/np.max(robustErrors),  c='brown')
    plt.plot(hues, gaussianErrors*y2/np.max(gaussianErrors),  c='purple')

    chThError.opendr_input = renderer
    lineStyles = ['-', '--', '-.', ':']

    # plt.axvline(np.mod(bestAzNormal*180/np.pi,360), linewidth=2, c='purple')
    # plt.axvline(np.mod(bestAzRobust*180/np.pi,360), linewidth=2, c='brown')
    # plt.axvline(bestHue, linewidth=2, c='y')
    plt.axvline(hueGT, linewidth=2,c='g')
    plt.axvline(huePred, linewidth=2,c='r')

    # plt.axvline(np.mod(currentAz*180/np.pi, 360), linewidth=2, linestyle='--',c='b')

    plt.xlabel('Sample')
    plt.ylabel('Angular error')

    plt.axis((0,255,y1,y2))
    plt.title('Neuralnet multiple predictions')
    fig.savefig(figurePath + 'sample' + '.png', bbox_inches='tight')
    plt.close(fig)

    chVColors[:] = currentVColors
    cv2.imwrite(figurePath + '_render.png', cv2.cvtColor(np.uint8(lin2srgb(renderer.r.copy())*255), cv2.COLOR_RGB2BGR))


def analyzeAz(figurePath, rendererGT, renderer, sampleEl, sampleVColor, sampleSH, sampleAzsPredictions=None, sampleStds=0.1):
    global stds
    global chAz
    global test_i
    global samplingMode

    plt.ioff()
    fig = plt.figure()

    stds[:] = sampleStds
    negLikModel = -ch.sum(generative_models.LogGaussianModel(renderer=renderer, groundtruth=rendererGT, variances=variances))
    negLikModelRobust = -ch.sum(generative_models.LogRobustModel(renderer=renderer, groundtruth=rendererGT, foregroundPrior=globalPrior, variances=variances))
    models = [negLikModel, negLikModelRobust, negLikModelRobust]
    errorFunRobust = models[1]
    errorFunGaussian = models[0]

    plt.hist(np.mod(sampleAzsPredictions*180/np.pi,360), bins=30, alpha=0.2)

    bestAz = testAzsRel[test_i]

    currentAz = chAz.r.copy()
    chEl[:] = sampleEl
    chVColors[:] = sampleVColor
    chLightSHCoeffs[:] = sampleSH

    trainingTeapots = [0,14,20,25,26,1]
    trainingTeapots = [0]
    azRange = np.arange(0,2*np.pi,5*np.pi/180)
    chThErrors = np.zeros([len(trainingTeapots), len(azRange)])

    robustErrors = np.array([])
    gaussianErrors = np.array([])
    angles = np.array([])
    for az_i, az in enumerate(azRange):
        angles = np.append(angles, az*180/np.pi)
        chAz[:] = az
        for idx, renderer_idx in enumerate(trainingTeapots):
            renderer_i = renderer_teapots[renderer_idx]
            rendererGray =  0.3*renderer_i[:,:,0] +  0.59*renderer_i[:,:,1] + 0.11*renderer_i[:,:,2]
            chThError.opendr_input = rendererGray
            chThErrors[idx, az_i] = chThError.r

        robustErrors = np.append(robustErrors, errorFunRobust.r)
        gaussianErrors = np.append(gaussianErrors, errorFunGaussian.r)

    x1,x2,y1,y2 = plt.axis()

    robustErrors = robustErrors - np.min(robustErrors)
    gaussianErrors = gaussianErrors - np.min(gaussianErrors)
    chThErrors = chThErrors - np.min(chThErrors)
    plt.plot(angles, robustErrors*y2/np.max(robustErrors),  c='brown')
    plt.plot(angles, gaussianErrors*y2/np.max(gaussianErrors),  c='purple')

    chThError.opendr_input = renderer
    lineStyles = ['-', '--', '-.', ':']
    for renderer_idx in range(len(trainingTeapots)):
        plt.plot(angles, chThErrors[renderer_idx]*y2/np.max(chThErrors[renderer_idx]), linestyle=lineStyles[np.mod(renderer_idx,4)], c='y')

    if len(trainingTeapots) > 1:
        prodErrors = np.prod(chThErrors, axis=0)
        plt.plot(angles, prodErrors*y2/np.max(prodErrors), linestyle='-', c='black')
        meanErrors = np.mean(chThErrors, axis=0)
        plt.plot(angles, meanErrors*y2/np.max(meanErrors), linestyle='--', c='black')
        # plt.plot(angles, gaussianErrors*robustErrors*y2/np.max(gaussianErrors*robustErrors), linestyle='--', c='black')

    # plt.axvline(np.mod(bestAzNormal*180/np.pi,360), linewidth=2, c='purple')
    # plt.axvline(np.mod(bestAzRobust*180/np.pi,360), linewidth=2, c='brown')
    plt.axvline(np.mod(bestAz*180/np.pi,360), linewidth=2, c='y')
    plt.axvline(testAzsRel[test_i]*180/np.pi, linewidth=2,c='g')
    plt.axvline(np.mod(azsPred[test_i]*180/np.pi, 360), linewidth=2,c='r')

    plt.axvline(np.mod(currentAz*180/np.pi, 360), linewidth=2, linestyle='--',c='b')

    plt.xlabel('Sample')
    plt.ylabel('Angular error')

    if samplingMode == False:

        scaleAzSamples = np.array(errorFunAzSamples)
        scaleAzSamples = scaleAzSamples - np.min(scaleAzSamples) + 1
        scaleAzSamples = scaleAzSamples*0.25*y2/np.max(scaleAzSamples)
        for azSample_i, azSample in enumerate(scaleAzSamples):
            plt.plot(np.mod(totalAzSamples[azSample_i]*180/np.pi, 360), azSample, marker='o', ms=20., c='r')

        scaleAzSamples = np.array(errorFunGaussianAzSamples)
        scaleAzSamples = scaleAzSamples - np.min(scaleAzSamples) + 1
        scaleAzSamples = scaleAzSamples*0.4*y2/np.max(scaleAzSamples)
        for azSample_i, azSample in enumerate(scaleAzSamples):
            plt.plot(np.mod(totalAzSamples[azSample_i]*180/np.pi, 360), azSample, marker='o', ms=20., c='g')

        scaleAzSamples = np.array(errorFunAzSamplesPred)
        scaleAzSamples = scaleAzSamples - np.min(scaleAzSamples) + 1
        scaleAzSamples = scaleAzSamples*0.65*y2/np.max(scaleAzSamples)
        for azSample_i, azSample in enumerate(scaleAzSamples):
            plt.plot(np.mod(totalAzSamples[azSample_i]*180/np.pi, 360), azSample, marker='o', ms=20., c='b')

        scaleAzSamples = np.array(errorFunGaussianAzSamplesPred)
        scaleAzSamples = scaleAzSamples - np.min(scaleAzSamples) + 1
        scaleAzSamples = scaleAzSamples*0.75*y2/np.max(scaleAzSamples)
        for azSample_i, azSample in enumerate(scaleAzSamples):
            plt.plot(np.mod(totalAzSamples[azSample_i]*180/np.pi, 360), azSample, marker='o', ms=20., c='y')

    plt.axis((0,360,y1,y2))
    plt.title('Neuralnet multiple predictions')
    fig.savefig(figurePath + 'sample' + '.png', bbox_inches='tight')
    plt.close(fig)

    chAz[:] = currentAz
    cv2.imwrite(figurePath + '_render.png', cv2.cvtColor(np.uint8(lin2srgb(renderer.r.copy())*255), cv2.COLOR_RGB2BGR))

#Fit:
print("Fitting predictions")

print("Using " + modelsDescr[model])
errorFun = models[model]
pixelErrorFun = pixelModels[model]

testSamples = 1
if recognitionType == 2:
    testSamples  = numSamples
predSamples = 50

chDisplacement[:] = np.array([0.0, 0.0,0.0])
chScale[:] = np.array([1.0,1.0,1.0])
chObjAz[:] = 0
shapeIm = [height, width]

#Update all error functions with the right renderers.
print("Using " + modelsDescr[model])

negLikModel = -ch.sum(generative_models.LogGaussianModel(renderer=renderer, groundtruth=rendererGT, variances=variances))
negLikModelRobust = -ch.sum(generative_models.LogRobustModel(renderer=renderer, groundtruth=rendererGT, foregroundPrior=globalPrior, variances=variances))
pixelLikelihoodCh = generative_models.LogGaussianModel(renderer=renderer, groundtruth=rendererGT, variances=variances)
pixelLikelihoodRobustCh = generative_models.LogRobustModel(renderer=renderer, groundtruth=rendererGT, foregroundPrior=globalPrior, variances=variances)

post = generative_models.layerPosteriorsRobustCh(rendererGT, renderer, np.array([]), 'FULL', globalPrior, variances)[0]

# hogGT, hogImGT, drconv = image_processing.diffHog(rendererGT)
# hogRenderer, hogImRenderer, _ = image_processing.diffHog(renderer, drconv)
#
# hogE_raw = hogGT - hogRenderer
# hogCellErrors = ch.sum(hogE_raw*hogE_raw, axis=2)
# hogError = ch.SumOfSquares(hogE_raw)

# modelLogLikelihoodRobustRegionCh = -ch.sum(generative_models.LogRobustModelRegion(renderer=renderer, groundtruth=rendererGT, foregroundPrior=globalPrior, variances=variances))/numPixels
#
# pixelLikelihoodRobustRegionCh = generative_models.LogRobustModelRegion(renderer=renderer, groundtruth=rendererGT, foregroundPrior=globalPrior, variances=variances)

# robPyr = opendr.filters.gaussian_pyramid(renderer - rendererGT, n_levels=6, normalization='size')
# robPyrSum = -ch.sum(ch.log(ch.exp(-0.5*robPyr**2/variances) + 1))

models = [negLikModel, negLikModelRobust]
pixelModels = [pixelLikelihoodCh, pixelLikelihoodRobustCh]
modelsDescr = ["Gaussian Model", "Outlier model" ]

errorFun = models[model]

testDescription = 'fontsize'
testPrefix = experimentPrefix + '_' + testDescription + '_' + optimizationTypeDescr[optimizationType] + '_' + str(len(testSet)) + 'samples_'

testPrefixBase = testPrefix

runExp = True
shapePenaltyTests = [0]
stdsTests = [0.1]
modelTests = len(stdsTests)*[1]
modelTests = [0]
methodTests = len(stdsTests)*[1]

nearestNeighbours = False

if nearestNeighbours:
    trainImages = readImages(imagesDir, trainIds, loadFromHdf5)
    trainImagesR = trainImages.reshape([len(trainImages), -1])

if includeMeanBaseline:
    methodsPred = ["Mean Baseline"]
    plotColors = ['k']

if nearestNeighbours:
    methodsPred = methodsPred + ["Nearest Neighbours"]
    plotColors = plotColors + ['g']

methodsPred = methodsPred + ["Recognition"]

plotColors = plotColors + ['b']

if optimizationTypeDescr[optimizationType] != 'predict':
    methodsPred = methodsPred + ["Fit"]
    plotColors = plotColors + ['r']


for testSetting, model in enumerate(modelTests):
    model = modelTests[testSetting]
    method = methodTests[testSetting]
    shapePenalty = shapePenaltyTests[testSetting]
    stds[:] = stdsTests[testSetting]

    testPrefix = testPrefixBase + '_method' + str(method)  + 'errorFun' + str(model) + '_std' + str(stds.r[0])  + '_shapePen'+ str(shapePenalty)

    resultDir = 'results/' + testPrefix + '/'

    if not os.path.exists(resultDir + 'imgs/'):
        os.makedirs(resultDir + 'imgs/')
    if not os.path.exists(resultDir +  'imgs/samples/'):
        os.makedirs(resultDir + 'imgs/samples/')

    ## NN individual prediction samples analysis.
    if not os.path.exists(resultDir + 'nn_samples/'):
        os.makedirs(resultDir + 'nn_samples/')

    if not os.path.exists(resultDir + 'az_samples/'):
        os.makedirs(resultDir + 'az_samples/')

    if not os.path.exists(resultDir + 'hue_samples/'):
        os.makedirs(resultDir + 'hue_samples/')


    azimuths = []
    elevations = []
    vColors = []
    lightCoeffs = []
    approxProjections = []
    likelihoods = []
    shapeParams = []
    posteriors = []

    startTime = time.time()
    samplingMode = False

    fittedVColorsList = []
    fittedRelLightCoeffsList = []

    approxProjectionsFittedList = []
    approxProjectionsGTList = []
    approxProjectionsPredList = []

    fittedAzs = np.array([])
    fittedElevs = np.array([])
    fittedRelLightCoeffs = []
    fittedShapeParamsList = []
    fittedVColors = []
    fittedPosteriorsList = []

    if nearestNeighbours:
        azimuthNearestNeighboursList = []
        elevationNearestNeighboursList = []
        vColorNearestNeighboursList = []
        shapeParamsNearestNeighboursList = []
        lightCoeffsNearestNeighboursList = []
        nearestNeighboursErrorFuns = np.array([])
        approxProjectionsNearestNeighbourList = []

        nearestNeighboursPosteriorsList = []

    errorsShapeVerticesSoFar = np.array([])

    predictedErrorFuns = np.array([])
    predictedPosteriorsList = []

    if includeMeanBaseline:
        meanBaselineErrorFuns = np.array([])
        meanBaselinePosteriorList = []

    errorsFittedShapeVertices = np.array([])
    fittedErrorFuns = np.array([])
    fittedShapeParams = np.array([])

    if (computePredErrorFuns and optimizationType == 0) or optimizationType != 0:
        for test_i in range(len(testAzsRel)):

            resultDir = 'results/' + testPrefix + '/'

            testOcclusions = dataOcclusions

            bestFittedAz = chAz.r
            bestFittedEl = chEl.r
            bestModelLik = np.finfo('f').max
            bestVColors = chVColors.r
            bestLightSHCoeffs = chLightSHCoeffs.r
            if useShapeModel:
                bestShapeParams = chShapeParams.r

            testId = dataIds[test_i]
            print("************** Minimizing loss of prediction " + str(test_i) + "of " + str(len(testAzsRel)))

            image = skimage.transform.resize(images[test_i], [height,width])
            imageSrgb = image.copy()
            rendererGT[:] = srgb2lin(image)

            negLikModel = -ch.sum(generative_models.LogGaussianModel(renderer=renderer, groundtruth=rendererGT, variances=variances))/numPixels
            negLikModelRobust = -ch.sum(generative_models.LogRobustModel(renderer=renderer, groundtruth=rendererGT, foregroundPrior=globalPrior, variances=variances))/numPixels

            models = [negLikModel, negLikModelRobust]

            stds[:] = stdsTests

            if nearestNeighbours:
                onenn_i = one_nn(trainImagesR, imageSrgb.ravel())
                nearesTrainImage = trainImages[onenn_i]
                cv2.imwrite(resultDir + 'imgs/test'+ str(test_i) + '/id' + str(testId) +'_nearestneighbour' + '.png', cv2.cvtColor(np.uint8(nearesTrainImage[0].copy()*255), cv2.COLOR_RGB2BGR))
                azimuthNearestNeighbour = trainAzsRel[onenn_i]
                elevationNearestNeighbour = trainElevsGT[onenn_i]
                vColorNearestNeighbour = trainVColorGT[onenn_i]
                if useShapeModel:
                    shapeParamsNearestNeighbour = trainShapeModelCoeffsGT[onenn_i]
                lightCoeffsNearestNeighbour = trainLightCoefficientsGTRel[onenn_i]

                azimuthNearestNeighboursList = azimuthNearestNeighboursList + [azimuthNearestNeighbour]
                elevationNearestNeighboursList = elevationNearestNeighboursList + [elevationNearestNeighbour]
                vColorNearestNeighboursList = vColorNearestNeighboursList + [vColorNearestNeighbour]
                shapeParamsNearestNeighboursList = shapeParamsNearestNeighboursList + [shapeParamsNearestNeighbour]
                lightCoeffsNearestNeighboursList = lightCoeffsNearestNeighboursList + [lightCoeffsNearestNeighbour]

                chAz[:] = azimuthNearestNeighbour
                chEl[:] = elevationNearestNeighbour
                chVColors[:] = vColorNearestNeighbour
                chLightSHCoeffs[:] = lightCoeffsNearestNeighbour
                if useShapeModel:
                    chShapeParams[:] = shapeParamsNearestNeighbour

                nearestNeighboursErrorFuns = np.append(nearestNeighboursErrorFuns, errorFun.r)

                nearestNeighboursPosteriorsList = nearestNeighboursPosteriorsList + [np.array(renderer.indices_image==1).copy().astype(np.bool)]


            if includeMeanBaseline:
                chAz[:] = meanTrainAzimuthRel[test_i]
                chEl[:] = meanTrainElevation[test_i]
                chVColors[:] = meanTrainVColors[test_i]
                chLightSHCoeffs[:] = meanTrainLightCoefficientsGTRel[test_i]
                if useShapeModel:
                    chShapeParams[:] = meanTrainShapeParams[test_i]

                meanBaselinePosteriorList = meanBaselinePosteriorList + [np.array(renderer.indices_image==1).copy().astype(np.bool)[None,:]]
                meanBaselineErrorFuns = np.append(meanBaselineErrorFuns, errorFun.r)

            stdsSmall = ch.Ch([0.01])
            variancesSmall = stdsSmall ** 2
            negLikModelRobustSmallStd = -ch.sum(generative_models.LogRobustModel(renderer=renderer, groundtruth=rendererGT, foregroundPrior=globalPrior, variances=variancesSmall))/numPixels

            if not os.path.exists(resultDir + 'imgs/test'+ str(test_i) + '/'):
                os.makedirs(resultDir + 'imgs/test'+ str(test_i) + '/')

            if not os.path.exists(resultDir + 'imgs/test'+ str(test_i) + '/SH/'):
                os.makedirs(resultDir + 'imgs/test'+ str(test_i) + '/SH/')

            cv2.imwrite(resultDir + 'imgs/test'+ str(test_i) + '/id' + str(testId) +'_groundtruth' + '.png', cv2.cvtColor(np.uint8(lin2srgb(rendererGT.r.copy())*255), cv2.COLOR_RGB2BGR))

            for sample in range(testSamples):

                if recognitionType == 0:
                    #Prediction from (near) ground truth.

                    color = testVColorGT[test_i] + nearGTOffsetVColor
                    az = testAzsRel[test_i] + nearGTOffsetRelAz
                    el = testElevsGT[test_i] + nearGTOffsetEl
                    lightCoefficientsRel = testLightCoefficientsGTRel[test_i]

                    if useShapeModel:
                        shapeParams = testShapeParamsGT[test_i]
                elif recognitionType == 1 or recognitionType == 2:

                    #Recognition estimate:
                    az = azsPred[test_i]
                    el = min(max(elevsPred[test_i],radians(1)), np.pi/2-radians(1))
                    color = vColorsPred[test_i]
                    lightCoefficientsRel = relLightCoefficientsPred[test_i]
                    if useShapeModel:
                        shapeParams = shapeParamsPred[test_i]

                chAz[:] = az
                chEl[:] = el
                chVColors[:] = color
                chLightSHCoeffs[:] = lightCoefficientsRel
                if useShapeModel:
                    chShapeParams[:] = shapeParams

                cv2.imwrite(resultDir + 'imgs/test'+ str(test_i) + '/sample' + str(sample) +  '_predicted'+ '.png', cv2.cvtColor(np.uint8(lin2srgb(renderer.r.copy())*255), cv2.COLOR_RGB2BGR))

                hdridx = dataEnvMaps[test_i]

                envMapTexture = np.zeros([360,180,3])
                envMapFound = False
                for hdrFile, hdrValues in hdritems:
                    if hdridx == hdrValues[0]:

                        envMapCoeffsGT = hdrValues[1]
                        envMapFilename = hdrFile

                        envMapTexture = np.array(imageio.imread(envMapFilename))[:,:,0:3]
                        envMapTexture = cv2.resize(src=envMapTexture, dsize=(360,180))
                        envMapFound = True
                        break

                if not envMapFound:
                    ipdb.set_trace()

                pEnvMap = SHProjection(envMapTexture, np.concatenate([testLightCoefficientsGTRel[test_i][:,None], testLightCoefficientsGTRel[test_i][:,None], testLightCoefficientsGTRel[test_i][:,None]], axis=1))
                approxProjectionGT = np.sum(pEnvMap, axis=(2,3))
                approxProjectionsGTList = approxProjectionsGTList + [approxProjectionGT[None,:]]

                cv2.imwrite(resultDir + 'imgs/test'+ str(test_i) + '/SH/' + str(hdridx) + '_GT.jpeg' , 255*np.sum(pEnvMap, axis=3)[:,:,[2,1,0]])

                pEnvMap = SHProjection(envMapTexture, np.concatenate([relLightCoefficientsPred[test_i][:,None], relLightCoefficientsPred[test_i][:,None], relLightCoefficientsPred[test_i][:,None]], axis=1))
                approxProjectionPred = np.sum(pEnvMap, axis=(2,3))

                approxProjectionsPredList = approxProjectionsPredList + [approxProjectionPred[None,:]]

                predictedPosteriorsList = predictedPosteriorsList + [np.array(renderer.indices_image==1).copy().astype(np.bool)[None,:]]

                if nearestNeighbours:
                    pEnvMap = SHProjection(envMapTexture, np.concatenate([lightCoeffsNearestNeighbour.ravel()[:,None], lightCoeffsNearestNeighbour.ravel()[:,None], lightCoeffsNearestNeighbour.ravel()[:,None]], axis=1))
                    approxProjectionNearestNeighbour = np.sum(pEnvMap, axis=(2,3))
                    approxProjectionsNearestNeighbourList = approxProjectionsNearestNeighbourList + [approxProjectionNearestNeighbour[None,:]]
                    cv2.imwrite(resultDir + 'imgs/test'+ str(test_i) + '/SH/' + str(hdridx) + '_NearestNeighbour.jpeg' , 255*np.sum(pEnvMap, axis=3)[:,:,[2,1,0]])

                cv2.imwrite(resultDir + 'imgs/test'+ str(test_i) + '/SH/' + str(hdridx) + '_Pred.jpeg' , 255*np.sum(pEnvMap, axis=3)[:,:,[2,1,0]])

                ## RecognitionType =2 : Use samples from neural net to explore the space better.
                if recognitionType == 2:
                    errorFunAzSamples = []
                    errorFunAzSamplesPred = []
                    errorFunGaussianAzSamplesPred = []
                    errorFunGaussianAzSamples = []

                    if not os.path.exists(resultDir + 'az_samples/test' + str(test_i) + '/'):
                        os.makedirs(resultDir + 'az_samples/test' + str(test_i) + '/')
                    if not os.path.exists(resultDir + 'hue_samples/test' + str(test_i) + '/'):
                        os.makedirs(resultDir + 'hue_samples/test' + str(test_i) + '/')
                    samplingMode = True
                    cv2.imwrite(resultDir + 'az_samples/test' + str(test_i)  + '_gt.png', cv2.cvtColor(np.uint8(lin2srgb(rendererGT.r.copy())*255), cv2.COLOR_RGB2BGR))
                    # stds[:] = 0.1
                    #
                    # azSampleStdev = np.std(azsPredictions[test_i])
                    azSampleStdev = np.sqrt(-np.log(np.min([np.mean(sinAzsPredSamples[test_i])**2 + np.mean(cosAzsPredSamples[test_i])**2,1])))
                    predAz = chAz.r
                    numSamples = max(int(np.ceil(azSampleStdev*180./(np.pi*25.))),1)
                    azSamples = np.linspace(0, azSampleStdev, numSamples)
                    totalAzSamples = predAz + np.concatenate([azSamples, -azSamples[1:]])
                    sampleAzNum  = 0

                    # model = 1
                    # errorFun = models[model]

                    bestPredAz = chAz.r
                    # bestPredEl = chEl.r
                    bestPredEl = min(max(chEl.r.copy(),radians(1)), np.pi/2-radians(1))
                    bestPredVColors = chVColors.r.copy()
                    bestPredLightSHCoeffs = chLightSHCoeffs.r.copy()
                    if useShapeModel:
                        bestPredShapeParams = chShapeParams.r.copy()
                    bestModelLik = np.finfo('f').max
                    bestPredModelLik = np.finfo('f').max
                    # analyzeAz(resultDir + 'az_samples/test' + str(test_i) +'/pre'  , rendererGT, renderer, chEl.r, chVColors.r, chLightSHCoeffs.r, azsPredictions[test_i], sampleStds=stds.r)

                    # analyzeHue(resultDir + 'hue_samples/test' + str(test_i) +'/pre', rendererGT, renderer, chEl.r, chAz.r, chLightSHCoeffs.r, vColorsPredSamples[test_i], sampleStds=stds.r)

                    for sampleAz in totalAzSamples:
                        global iterat
                        iterat = 0
                        sampleAzNum += 1

                        chAz[:] = sampleAz
                        # chEl[:] = elsample
                        print("Minimizing first step")
                        model = 1
                        errorFun = models[model]
                        # method = 1

                        chLightSHCoeffs[:] = lightCoefficientsRel
                        chVColors[:] = color
                        #Todo test with adding chEl.
                        free_variables = [chLightSHCoeffs]
                        options={'disp':False, 'maxiter':2}

                        errorFunAzSamplesPred = errorFunAzSamplesPred + [errorFun.r]
                        errorFunGaussianAzSamplesPred = errorFunGaussianAzSamplesPred + [models[0].r]

                        # analyzeAz(resultDir + 'az_samples/test' + str(test_i) +'/azNum' + str(sampleAzNum), rendererGT, renderer, chEl.r, chVColors.r, chLightSHCoeffs.r, azsPredictions[test_i], sampleStds=stds.r)

                        if models[1].r.copy() < bestPredModelLik:

                            print("Found best angle!")
                            # bestPredModelLik = errorFun.r.copy()
                            bestPredModelLik = models[1].r.copy()
                            bestPredAz = sampleAz
                            bestPredEl = min(max(chEl.r.copy(),radians(1)), np.pi/2-radians(1))
                            bestPredVColors = chVColors.r.copy()
                            bestPredLightSHCoeffs = chLightSHCoeffs.r.copy()
                            if useShapeModel:
                                bestPredShapeParams = chShapeParams.r.copy()
                            bestModelLik = errorFun.r.copy()

                            # cv2.imwrite(resultDir + 'imgs/test'+ str(test_i) + '/best_predSample' + str(numPredSamples) + '.png', cv2.cvtColor(np.uint8(lin2srgb(renderer.r.copy())*255), cv2.COLOR_RGB2BGR))

                        errorFunAzSamples = errorFunAzSamples + [errorFun.r]
                        errorFunGaussianAzSamples = errorFunGaussianAzSamples + [models[0].r]

                    color = bestPredVColors
                    lightCoefficientsRel = bestPredLightSHCoeffs
                    az = bestPredAz
                    if useShapeModel:
                        shapeParams = bestShapeParams

                    # previousAngles = np.vstack([previousAngles, np.array([[azsample, elsample],[chAz.r.copy(), chEl.r.copy()]])])

                    samplingMode = False
                    chAz[:] = az
                    # analyzeAz(resultDir + 'az_samples/test' + str(test_i) +'_samples', rendererGT, renderer, chEl.r, color, lightCoefficientsRel, azsPredictions[test_i], sampleStds=stds.r)

                chAz[:] = az
                chEl[:] = min(max(el,radians(1)), np.pi/2-radians(1))
                chVColors[:] = color
                chLightSHCoeffs[:] = lightCoefficientsRel.copy()
                if useShapeModel:
                    chShapeParams[:] = shapeParams

                cv2.imwrite(resultDir + 'imgs/test'+ str(test_i) + '/best_sample' + '.png', cv2.cvtColor(np.uint8(lin2srgb(renderer.r.copy())*255), cv2.COLOR_RGB2BGR))

                predictedErrorFuns = np.append(predictedErrorFuns, errorFun.r)

                global iterat
                iterat = 0

                sampleAzNum = 0

                sys.stdout.flush()

                ## finally: Do Fitting!

                if optimizationTypeDescr[optimizationType] == 'optimize':
                    print("** Minimizing from initial predicted parameters. **")
                    globalPrior[:] = 0.9

                    errorFun = models[modelTests[testSetting]]

                    free_variables = [chShapeParams, chAz, chEl, chLightSHCoeffs]
                    stds[:] = 0.03
                    shapePenalty = 0.0001
                    options={'disp':False, 'iter':50}

                    minimizingShape = True
                    ch.minimize({'raw': errorFun  + shapePenalty*ch.sum(chShapeParams**2)}, bounds=None, method=methods[method], x0=free_variables, callback=cb, options=options)

                    maxShapeSize = 2.5
                    largeShapeParams = np.abs(chShapeParams.r) > maxShapeSize
                    if np.any(largeShapeParams):
                        print("Warning: found large shape parameters to fix!")
                    chShapeParams[largeShapeParams] = np.sign(chShapeParams.r[largeShapeParams])*maxShapeSize


                    free_variables = [chShapeParams, chAz, chEl, chVColors, chLightSHCoeffs]
                    stds[:] = stdsTests[testSetting]
                    shapePenalty = 0.0
                    options={'disp':False, 'iter':50}
                    # free_variables = [chShapeParams ]
                    minimizingShape = True
                    ch.minimize({'raw': errorFun  + shapePenalty*ch.sum(chShapeParams**2)}, bounds=None, method=methods[method], x0=free_variables, callback=cb, options=options)

                    maxShapeSize = 2.5
                    largeShapeParams = np.abs(chShapeParams.r) > maxShapeSize
                    if np.any(largeShapeParams):
                        print("Warning: found large shape parameters to fix!")
                    chShapeParams[largeShapeParams] = np.sign(chShapeParams.r[largeShapeParams])*maxShapeSize

                    cv2.imwrite(resultDir + 'imgs/test'+ str(test_i) + '/it4'+ '.png', cv2.cvtColor(np.uint8(lin2srgb(renderer.r.copy())*255), cv2.COLOR_RGB2BGR))

                if errorFun.r < bestModelLik:
                    bestModelLik = errorFun.r.copy()
                    bestFittedAz = chAz.r.copy()
                    bestFittedEl = min(max(chEl.r.copy(),radians(1)), np.pi/2-radians(1))
                    bestVColors = chVColors.r.copy()
                    bestLightSHCoeffs = chLightSHCoeffs.r.copy()
                    if useShapeModel:
                        bestShapeParams = chShapeParams.r.copy()

                    cv2.imwrite(resultDir + 'imgs/test'+ str(test_i) + '/best'+ '.png', cv2.cvtColor(np.uint8(lin2srgb(renderer.r.copy())*255), cv2.COLOR_RGB2BGR))
                else:
                    pass
                    # bestFittedAz = bestPredAz.copy()
                    # bestFittedEl = min(max(bestPredEl.copy(),radians(1)), np.pi/2-radians(1))
                    # bestVColors = bestPredVColors.copy()
                    # bestLightSHCoeffs = bestPredLightSHCoeffs.copy()

                chAz[:] = bestFittedAz
                chEl[:] = min(max(bestFittedEl,radians(1)), np.pi/2-radians(1))
                chVColors[:] = bestVColors
                chLightSHCoeffs[:] = bestLightSHCoeffs
                if useShapeModel:
                    chShapeParams[:] = bestShapeParams

                cv2.imwrite(resultDir + 'imgs/test'+ str(test_i) + '/fitted'+ '.png',cv2.cvtColor(np.uint8(lin2srgb(renderer.r.copy())*255), cv2.COLOR_RGB2BGR))

            if optimizationTypeDescr[optimizationType] != 'predict':
                fittedErrorFuns = np.append(fittedErrorFuns, bestModelLik)
                fittedAzs = np.append(fittedAzs, bestFittedAz)
                fittedElevs = np.append(fittedElevs, bestFittedEl)
                fittedVColorsList = fittedVColorsList + [bestVColors]
                fittedRelLightCoeffsList = fittedRelLightCoeffsList + [bestLightSHCoeffs]
                if useShapeModel:
                    fittedShapeParamsList = fittedShapeParamsList + [bestShapeParams]

                pEnvMap = SHProjection(envMapTexture, np.concatenate([bestLightSHCoeffs[:,None], bestLightSHCoeffs[:,None], bestLightSHCoeffs[:,None]], axis=1))
                approxProjectionFitted = np.sum(pEnvMap, axis=(2,3))
                approxProjectionsFittedList = approxProjectionsFittedList + [approxProjectionFitted[None,:]]
                cv2.imwrite(resultDir + 'imgs/test'+ str(test_i) + '/SH/' + str(hdridx) + '_Fitted.jpeg' , 255*np.sum(pEnvMap, axis=3)[:,:,[2,1,0]])

                stds[:] = stdsTests[testSetting]
                vis_im = np.array(renderer.indices_image==1).copy().astype(np.bool)
                post = generative_models.layerPosteriorsRobustCh(rendererGT, renderer, vis_im, 'MASK', globalPrior, variances)[0]>0.5
                fittedPosteriorsList = fittedPosteriorsList + [post[None,:]]
                ipdb.set_trace()

                plt.imsave(resultDir + 'imgs/test'+ str(test_i) + '/' + str(hdridx) + '_Outlier.jpeg', np.tile(post.reshape(shapeIm[0],shapeIm[1],1), [1,1,3]))

            #Every now and then (or after the final test case), produce plots to keep track of work accross different levels of occlusion.
            if np.mod(test_i+1,100) == 0 or test_i + 1 >= len(testSet):
                if approxProjectionsPredList:
                    approxProjectionsPred = np.vstack(approxProjectionsPredList)
                if approxProjectionsGTList:
                    approxProjectionsGT = np.vstack(approxProjectionsGTList)

                if predictedPosteriorsList:
                    predictedPosteriors = np.vstack(predictedPosteriorsList)

                if nearestNeighbours:
                    approxProjectionsNearestNeighbours = np.vstack(approxProjectionsNearestNeighbourList)

                if optimizationTypeDescr[optimizationType] != 'predict':
                    if fittedVColorsList:
                        fittedVColors = np.vstack(fittedVColorsList)
                    if fittedRelLightCoeffsList:
                        fittedRelLightCoeffs = np.vstack(fittedRelLightCoeffsList)
                    if approxProjectionsFittedList:
                        approxProjectionsFitted = np.vstack(approxProjectionsFittedList)

                    if fittedShapeParamsList and useShapeModel:
                        fittedShapeParams = np.vstack(fittedShapeParamsList)
                    if fittedPosteriorsList:
                        fittedPosteriors = np.vstack(fittedPosteriorsList)

                if nearestNeighbours:
                    azimuthNearestNeighbours = np.concatenate(azimuthNearestNeighboursList)
                    elevationNearestNeighbours = np.concatenate(elevationNearestNeighboursList)
                    vColorNearestNeighbours = np.vstack(vColorNearestNeighboursList)
                    shapeParamsNearestNeighbours = np.vstack(shapeParamsNearestNeighboursList)
                    lightCoeffsNearestNeighbours = np.vstack(lightCoeffsNearestNeighboursList)
                    nearestNeighboursPosteriors = np.vstack(nearestNeighboursPosteriorsList)

                if optimizationTypeDescr[optimizationType] != 'predict':
                    numFitted = range(len(fittedAzs))
                else:
                    numFitted = range(len(approxProjectionsPred))

                if includeMeanBaseline:
                    meanBaselinePosteriors = np.vstack(meanBaselinePosteriorList)

                    azimuths = [meanTrainAzimuthRel]
                    elevations= [meanTrainElevation]
                    vColors= [meanTrainVColors]
                    lightCoeffs= [meanTrainLightCoefficientsGTRel]
                    approxProjections= [meanTrainEnvMapProjections]
                    likelihoods = [meanBaselineErrorFuns]
                    posteriors = [meanBaselinePosteriors]

                if useShapeModel:
                    shapeParams= [meanTrainShapeParams]
                else:
                    shapeParams = [None]

                if nearestNeighbours:
                    azimuths = azimuths + [azimuthNearestNeighbours]
                    elevations = elevations + [elevationNearestNeighbours]
                    vColors = vColors + [vColorNearestNeighbours]
                    lightCoeffs = lightCoeffs + [lightCoeffsNearestNeighbours]
                    approxProjections = approxProjections + [approxProjectionsNearestNeighbours]
                    if useShapeModel:
                        shapeParams  = shapeParams + [shapeParamsNearestNeighbours]
                    else:
                        shapeParams = shapeParams + [None]

                    likelihoods = likelihoods + [nearestNeighboursErrorFuns]
                    posteriors = posteriors + [nearestNeighboursPosteriors]

                azimuths = azimuths + [azsPred]
                elevations = elevations + [elevsPred]
                vColors = vColors + [vColorsPred]
                lightCoeffs = lightCoeffs + [relLightCoefficientsPred]
                approxProjections = approxProjections + [approxProjectionsPred]
                likelihoods = likelihoods + [predictedErrorFuns]
                posteriors = posteriors + [predictedPosteriors]

                if useShapeModel:
                    shapeParams  = shapeParams + [shapeParamsPred]
                else:
                    shapeParams = shapeParams + [None]

                if optimizationTypeDescr[optimizationType] != 'predict':
                    azimuths = azimuths + [fittedAzs]
                    elevations = elevations + [fittedElevs]
                    vColors = vColors + [fittedVColors]
                    lightCoeffs = lightCoeffs + [fittedRelLightCoeffs]
                    approxProjections = approxProjections + [approxProjectionFitted]
                    if useShapeModel:
                        shapeParams  = shapeParams + [fittedShapeParams]
                    else:
                        shapeParams = shapeParams + [None]

                    likelihoods = likelihoods + [fittedErrorFuns]
                    posteriors = posteriors + [fittedPosteriors]

                errorsPosePredList, errorsLightCoeffsList, errorsShapeParamsList, errorsShapeVerticesList, errorsEnvMapList, errorsLightCoeffsCList, errorsVColorsEList, errorsVColorsCList, errorsSegmentation \
                    = computeErrors(numFitted, azimuths, testAzsRel, elevations, testElevsGT, vColors, testVColorGT, lightCoeffs, testLightCoefficientsGTRel, approxProjections,  approxProjectionsGT, shapeParams, testShapeParamsGT, useShapeModel, chShapeParams, chVertices, posteriors, masksGT)

                meanAbsErrAzsList, meanAbsErrElevsList, medianAbsErrAzsList, medianAbsErrElevsList, meanErrorsLightCoeffsList, meanErrorsShapeParamsList, meanErrorsShapeVerticesList, meanErrorsLightCoeffsCList, meanErrorsEnvMapList, meanErrorsVColorsEList, meanErrorsVColorsCList, meanErrorsSegmentation \
                    = computeErrorMeans(numFitted, useShapeModel, errorsPosePredList, errorsLightCoeffsList, errorsShapeParamsList, errorsShapeVerticesList, errorsEnvMapList, errorsLightCoeffsCList, errorsVColorsEList, errorsVColorsCList, errorsSegmentation)

                #Write statistics to file.
                with open(resultDir + 'performance.txt', 'w') as expfile:
                    for method_i in range(len(azimuths)):
                        # expfile.write(str(z))
                        expfile.write("Avg" + methodsPred[method_i] + "NLL    :" +  str(np.mean(likelihoods[method_i]))+ '\n')
                        expfile.write("Mean Azimuth Error " + methodsPred[method_i] + " " +  str(meanAbsErrAzsList) + '\n')
                        expfile.write("Mean Elevation Error " + methodsPred[method_i] + " " +  str(meanAbsErrElevsList[method_i])+ '\n')
                        expfile.write("Median Azimuth Error " + methodsPred[method_i] + " " +  str(medianAbsErrAzsList[method_i]) + '\n')
                        expfile.write("Median Elevation Error " + methodsPred[method_i] + " " +  str(medianAbsErrElevsList[method_i])+ '\n\n')
                        expfile.write("Mean SH Components Error " + methodsPred[method_i] + " " +  str(meanErrorsLightCoeffsList[method_i])+ '\n')
                        expfile.write("Mean SH Components Error " + methodsPred[method_i] + " " +  str(meanErrorsLightCoeffsCList[method_i])+ '\n')
                        expfile.write("Mean Vertex Colors Error E " + methodsPred[method_i] + " " +  str(meanErrorsVColorsEList[method_i])+ '\n')
                        expfile.write("Mean Vertex Colors Error C " + methodsPred[method_i] + " " +  str(meanErrorsVColorsCList[method_i])+ '\n')
                        expfile.write("Mean Shape Error " + methodsPred[method_i] + " " +  str(meanErrorsShapeParamsList[method_i])+ '\n')
                        expfile.write("Mean Shape Vertices Error " + methodsPred[method_i] + " " +  str(meanErrorsShapeVerticesList[method_i])+ '\n\n')

                if not os.path.exists(resultDir + 'stats/'):
                    os.makedirs(resultDir + 'stats/')

                with open(resultDir + 'stats/' + 'performance' + str(test_i) + '.txt', 'w') as expfile:
                    # expfile.write(str(z))
                    expfile.write("Avg" + methodsPred[method_i] + "NLL    :" +  str(np.mean(likelihoods[method_i]))+ '\n')
                    for method_i in range(len(azimuths)):
                        expfile.write("Mean Azimuth Error " + methodsPred[method_i] + " " +  str(meanAbsErrAzsList) + '\n')
                        expfile.write("Mean Elevation Error " + methodsPred[method_i] + " " +  str(meanAbsErrElevsList[method_i])+ '\n')
                        expfile.write("Median Azimuth Error " + methodsPred[method_i] + " " +  str(medianAbsErrAzsList[method_i]) + '\n')
                        expfile.write("Median Elevation Error " + methodsPred[method_i] + " " +  str(medianAbsErrElevsList[method_i])+ '\n\n')
                        expfile.write("Mean SH Components Error " + methodsPred[method_i] + " " +  str(meanErrorsLightCoeffsList[method_i])+ '\n')
                        expfile.write("Mean SH Components Error " + methodsPred[method_i] + " " +  str(meanErrorsLightCoeffsCList[method_i])+ '\n')
                        expfile.write("Mean Vertex Colors Error E " + methodsPred[method_i] + " " +  str(meanErrorsVColorsEList[method_i])+ '\n')
                        expfile.write("Mean Vertex Colors Error C " + methodsPred[method_i] + " " +  str(meanErrorsVColorsCList[method_i])+ '\n')
                        expfile.write("Mean Shape Error " + methodsPred[method_i] + " " +  str(meanErrorsShapeParamsList[method_i])+ '\n')
                        expfile.write("Mean Shape Vertices Error " + methodsPred[method_i] + " " +  str(meanErrorsShapeVerticesList[method_i])+ '\n\n')

                # ipdb.set_trace()
                totalTime = time.time() - startTime
                print("Took " + str(totalTime/test_i) + " time per instance.")

                experimentDic = {'testSet':testSet, 'methodsPred':methodsPred, 'testOcclusions':testOcclusions, 'testPrefixBase':testPrefixBase, 'likelihoods':likelihoods, 'posteriors':posteriors, 'parameterRecognitionModels':parameterRecognitionModels, 'azimuths':azimuths, 'elevations':elevations, 'vColors':vColors, 'lightCoeffs':lightCoeffs, 'approxProjections':approxProjections, 'shapeParams':shapeParams, 'approxProjectionsGT':approxProjectionsGT, 'errorsPosePredList':errorsPosePredList, 'errorsLightCoeffsList':errorsLightCoeffsList, 'errorsShapeParamsLis':errorsShapeParamsList, 'errorsShapeVerticesList':errorsShapeVerticesList, 'errorsEnvMapList':errorsEnvMapList, 'errorsLightCoeffsCList':errorsLightCoeffsCList, 'errorsVColorsEList':errorsVColorsEList, 'errorsVColorsCList':errorsVColorsCList, 'errorsSegmentation':errorsSegmentation}

                with open(resultDir + 'experiment.pickle', 'wb') as pfile:
                    pickle.dump(experimentDic, pfile)

                # if optimizationTypeDescr[optimizationType] != 'predict':
                #     print("Avg Likelihood improvement per second of: " + str(np.mean(fittedErrorFuns - predictedErrorFuns)/ totalTime))
                    ##Print and plotting results now:
