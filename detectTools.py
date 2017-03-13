#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import functools
import os

import cv2

basePath = os.path.abspath(os.path.dirname(__name__))
buildPath = os.path.join(basePath, "build")
os.path.exists(buildPath) or os.makedirs(buildPath)


def is_folder(func):
    @functools.wraps(func)
    def wrapper(imagePath):
        if os.path.isdir(imagePath):
            for path, _, filelist in os.walk(imagePath):
                for name in filter(is_image_file, filelist):
                    func(os.path.join(path, name))
        else:
            return func(imagePath)

    return wrapper


def is_image_file(filename, extensions=[".jpg", ".jpeg", ".gif", ".png"]):
    return any(filename.lower().endswith(e) for e in extensions)


class Common(object):
    @staticmethod
    def str2int(char):
        return str(char) if isinstance(char, int) else str(ord(char))

    @staticmethod
    @is_folder
    def encrypt(fileName):
        with open(fileName, "rb") as rf:
            fileName = os.path.split(fileName)[-1]
            fileName = "encrypt_{}.txt".format(fileName.rsplit(".", 1)[0])
            with open(os.path.join(buildPath, fileName), "wb") as wf:
                translist = [Common.str2int(item) for item in rf.read()]
                wf.write("|".join(translist))

    @staticmethod
    @is_folder
    def decrypt(fileName):
        with open(fileName, "rb") as rf:
            file_ = rf.read()
            fileName = os.path.split(fileName)[-1]
            fileName = "decrypt_{}.jpg".format(fileName.rsplit(".", 1)[0])
            with open(os.path.join(buildPath, fileName), "wb") as wf:
                translist = [chr(int(item)) for item in file_.split("|")]
                wf.write("".join(translist))


def faceConfig():
    cascPath = os.path.join(basePath, "haarcascade_frontalface_default.xml")

    if not os.path.exists(cascPath):
        import urllib
        download_config = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
        urllib.urlretrieve(download_config, "haarcascade_frontalface_default.xml")

    return cv2.CascadeClassifier(cascPath)


@is_folder
def detectFaces(imagePath):
    faceCascade = faceConfig()

    image = cv2.imread(imagePath)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    """
        scaleFactor – Parameter specifying how much the image size is reduced at each image scale.
        minNeighbors – Parameter specifying how many neighbors each candidate rectangle should have to retain it.
        flags – Parameter with the same meaning for an old cascade as in the function cvHaarDetectObjects. It is not used for a new cascade.
        minSize – Minimum possible object size. Objects smaller than that are ignored.
        maxSize – Maximum possible object size. Objects larger than that are ignored.
    """
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.25,
        minNeighbors=5,
        minSize=(45, 45)
        # flags = cv2.CV_HAAR_SCALE_IMAGE
    )

    print("Found {0} faces!".format(len(faces)))

    for idx, (x, y, w, h) in enumerate(faces):
        # Draw a rectangle around the faces
        # cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 1)

        # trans to 120x120
        crop_img = image[y:y + h, x:x + w]
        resize_crop_img = cv2.resize(crop_img, (120, 120))

        # Save new img
        fileName = imagePath.rsplit("\\", 1)[1]
        savePath = os.path.join(buildPath, "%s_%s" % (idx, fileName))
        cv2.imwrite(savePath, resize_crop_img)

        # Call encrypt
        Common.encrypt(savePath)

    # cv2.imshow("Faces found", image)
    cv2.waitKey(0)


def main():
    parser = argparse.ArgumentParser(description="Detect faces using openCV.")
    parser.add_argument("-i", dest="input", required=True, help="input imagine")
    parser.add_argument("-e", dest="encrypt", required=False, action="store_true",
                        help="encrypt imagine")
    parser.add_argument("-d", dest="decrypt", required=False, action="store_true",
                        help="decrypt txt")

    args = parser.parse_args()

    if args.encrypt:
        return Common.encrypt(args.input)
    elif args.decrypt:
        return Common.decrypt(args.input)

    if args.input:
        return detectFaces(args.input)


if __name__ == "__main__":
    main()
