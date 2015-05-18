import cv2
import numpy
import matplotlib.pyplot as plt
import ipdb
import scipy
def scoreImage(img, template, method, methodParams):
    score = 0

    if method == 'chamferModelToData':
        sqDists = chamferDistanceModelToData(img, template, methodParams['minThresImage'], methodParams['maxThresImage'], methodParams['minThresTemplate'],methodParams['maxThresTemplate'])
        score = numpy.sum(sqDists)
    elif method == 'robustChamferModelToData':
        sqDists = numpy.sum(chamferDistanceModelToData(img, template, methodParams['minThresImage'], methodParams['maxThresImage'], methodParams['minThresTemplate'],methodParams['maxThresTemplate']))
        score = robustDistance(sqDists, methodParams['scale'])
    elif method == 'chamferDataToModel':
        sqDists = chamferDistanceDataToModel(img, template, methodParams['minThresImage'], methodParams['maxThresImage'], methodParams['minThresTemplate'],methodParams['maxThresTemplate'])
        score = numpy.sum(sqDists)
    elif method == 'robustChamferDataToModel':
        sqDists = numpy.sum(chamferDistanceDataToModel(img, template, methodParams['minThresImage'], methodParams['maxThresImage'], methodParams['minThresTemplate'],methodParams['maxThresTemplate']))
        score = robustDistance(sqDists, methodParams['scale'])
    elif method == 'sqDistImages':
        sqDists = sqDistImages(img, template)
        score = numpy.sum(sqDists) / template.size
    elif method == 'ignoreSqDistImages':
        sqDists = sqDistImages(img, template)
        score = numpy.sum(sqDists * (template > 0)) / numpy.sum(template > 0)
    elif method == 'robustSqDistImages':
        sqDists = sqDistImages(img, template)
        score = robustDistance(sqDists, methodParams['scale'])

    return score


def chamferDistanceModelToData(img, template, minThresImage, maxThresImage, minThresTemplate, maxThresTemplate):
    imgEdges = cv2.Canny(numpy.uint8(img*255), minThresImage,maxThresImage)

    tempEdges = cv2.Canny(numpy.uint8(template*255), minThresTemplate, maxThresTemplate)

    bwEdges1 = cv2.distanceTransform(~imgEdges, cv2.DIST_L2, 5)

    # cv2.imshow('ImageWindow',numpy.uint8(img*255))

    # cv2.waitKey()

    # cv2.imshow('ImageWindow',numpy.uint8(template*255))

    # cv2.waitKey()

    # cv2.imshow('ImageWindow',~tempEdges)

    # cv2.waitKey()

    # ipdb.set_trace()

    # disp = cv2.normalize(bwEdges1, bwEdges1, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)

    # cv2.imshow('ImageWindow', disp)

    # cv2.waitKey()

    score = numpy.sum(numpy.multiply(tempEdges/255, bwEdges1))/numpy.sum(tempEdges/255.0)

    return score




def chamferDistanceDataToModel(img, template, minThresImage, maxThresImage, minThresTemplate, maxThresTemplate):
    imgEdges = cv2.Canny(numpy.uint8(img*255), minThresImage,maxThresImage)

    tempEdges = cv2.Canny(numpy.uint8(template*255), minThresTemplate, maxThresTemplate)

    bwEdges1 = cv2.distanceTransform(~tempEdges, cv2.DIST_L2, 5)

    score = numpy.multiply(imgEdges/255.0, bwEdges1)/numpy.sum(imgEdges/255.0)

    return score


def sqDistImages(img, template):
    sqResiduals = numpy.square(img - template)
    return sqResiduals

def computeVariance(sqResiduals):
    return numpy.sum(sqResiduals)/len(sqResiduals)

def pixelWiseLayerPriors(masks):

    return numpy.sum(masks) / len(masks)

def modelLogLikelihood(image, template, pixelWiseLayerPriors, variances):

    return numpy.log(numpy.multiply(pixelWiseLayerPriors, scipy.stats.norm.pdf(image, location = template, scale=numpy.sqrt(variances) )) + (1 - pixelWiseLayerPriors))

def pixelWiseLayerPosteriors(img, template):
    fgCond = numpy.multiply(pixelWiseLayerPriors, scipy.stats.norm.pdf(image, location = template, scale=numpy.sqrt(variances) ))
    bgCond = (1 - pixelWiseLayerPriors)
    return fgCond/numpy.exp(modelLogLikelihood), bgCond/numpy.exp(modelLogLikelihood)


def robustDistance(sqResiduals, scale):
    return numpy.sum(sqResiduals/(sqResiduals + scale**2))





def testImageMatching():
    minThresTemplate = 10
    maxThresTemplate = 100
    methodParams = {'scale': 85000, 'minThresImage': minThresTemplate, 'maxThresImage': maxThresTemplate, 'minThresTemplate': minThresTemplate, 'maxThresTemplate': maxThresTemplate}
            
            

    teapots = ["test/teapot1", "test/teapot2","test/teapot3","test/teapot4","test/teapot5","test/teapot6"]

    images = []
    edges = []
    for teapot in teapots:
        im = cv2.imread(teapot + ".png")
        can = cv2.Canny(im, minThresTemplate,maxThresTemplate)
        images.append(im)
        edges.append(can)
        cv2.imwrite(teapot + "_can.png", can)

    confusion = numpy.zeros([6,6])
    for tp1 in numpy.arange(1,7):
        for tp2 in numpy.arange(tp1,7):
            dist = distance = scoreImage(images[tp1-1], images[tp2-1], 'robustSqDistImages', methodParams)
            print(dist)
            confusion[tp1-1, tp2-1] = dist

    plt.matshow(confusion)
    plt.colorbar()
    plt.savefig('test/confusion.png')





# elif method == 'chamferDataToModel':
#         sqDists = chamferDistanceDataToModel(img, template, methodParams['minThresImage'], methodParams['maxThresImage'], methodParams['minThresTemplate'],methodParams['maxThresTemplate'])
#         score = numpy.sum(sqDists)
#     elif method == 'robustChamferDataToModel':
#         sqDists = numpy.sum(chamferDistanceDataToModel(img, template, methodParams['minThresImage'], methodParams['maxThresImage'], methodParams['minThresTemplate'],methodParams['maxThresTemplate']))
#         score = robustDistance(sqDists, methodParams['robustScale'])
#     elif method == 'sqDistImages':
#         sqDists = sqDistImages(img, template)
#         score = numpy.sum(sqDists)
#     elif method == 'robustSqDistImages':