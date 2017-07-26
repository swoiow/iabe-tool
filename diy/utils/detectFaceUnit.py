#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import functools
import os
from distutils.version import StrictVersion

try:
    import cv2
    import numpy as np

    CV_VERSION = cv2.__version__
except ImportError as e:
    CV_VERSION = "2.0"
    # raise Exception(e)

if StrictVersion(CV_VERSION) > StrictVersion("2.0"):
    cv2.CV_LOAD_IMAGE_COLOR = cv2.IMREAD_COLOR
    __version__ = (3, 0)
else:
    __version__ = (2, 0)

base_dir = os.environ.get("IABE_IMG_DIR", os.path.abspath(os.path.dirname(__file__)))
build_dir = os.path.join(base_dir, "enc_data")
os.path.exists(build_dir) or os.makedirs(build_dir)


def is_folder(func):
    @functools.wraps(func)
    def wrapper(image_path):
        if os.path.isdir(image_path):
            for path, _, filelist in os.walk(image_path):
                for name in filter(is_image_file, filelist):
                    func(os.path.join(path, name))
        else:
            return func(image_path)

    return wrapper


def is_image_file(filename, extensions=None):
    if not extensions:
        extensions = [".jpg", ".jpeg", ".gif", ".png"]
    return any(filename.lower().endswith(i) for i in extensions)


class DetectFace(object):
    @staticmethod
    def str2int(char):
        return str(char) if isinstance(char, int) else str(ord(char))

    @staticmethod
    @is_folder
    def encrypt(file_name):
        enc_data = DetectFace._encrypt(file_name=file_name)

        file_name = os.path.split(file_name)[-1]
        file_name = "enc_{}.txt".format(file_name.rsplit(".", 1)[0])
        save_path = os.path.join(build_dir, file_name)
        with open(save_path, "w") as wf:
            wf.write(enc_data)

        return dict(data=enc_data, path=save_path, src_path=file_name)

    @staticmethod
    @is_folder
    def decrypt(file_name):
        with open(file_name, "r") as rf:
            dec_data = DetectFace._decrypt(rf.read())

            file_name = os.path.split(file_name)[-1]
            file_name = "dec_{}.jpg".format(file_name.rsplit(".", 1)[0])
            save_path = os.path.join(build_dir, file_name)
            with open(save_path, "wb") as wf:
                wf.write(dec_data)  # bug

        return save_path

    @staticmethod
    def _encrypt(file_name=None, buff=None):
        assert file_name or buff
        if file_name:
            with open(file_name, "rb") as rf:
                if __version__ == (2, 0):
                    translist = [DetectFace.str2int(item) for item in rf.read()]
                    return "|".join(translist)
                else:
                    return "|".join(map(str, list(rf.read())))
        elif buff:
            translist = [DetectFace.str2int(item) for item in buff.tostring()]
            return "|".join(translist)

    @staticmethod
    def _decrypt(string):
        translist = [int(item) for item in string.split("|")]
        if __version__ == (3, 0):
            return bytearray(iter(translist))

        return "".join(map(chr, translist))


def _face_config():
    cfg_path = os.path.join(base_dir, "..","face_default.cfg")

    if not os.path.exists(cfg_path):
        import urllib.request

        config_url = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
        urllib.request.urlretrieve(config_url, cfg_path)

    return cv2.CascadeClassifier(cfg_path)


@is_folder
def detect_faces(image_path=None, image_buff=None):
    result = []
    for idx, resize_crop_img in _detect_faces(image_path, image_buff):
        # Save new img
        file_name = os.path.basename(image_path)
        save_path = os.path.join(build_dir, "%s_%s" % (idx, file_name))
        cv2.imwrite(save_path, resize_crop_img)

        # Call encrypt
        r = DetectFace.encrypt(save_path)
        if r:
            result.append(dict(path=r["path"], src=r["src_path"]))

    # cv2.imshow("Faces found", image)
    # cv2.waitKey(0)  # comment because linux error

    return result


def main():
    parser = argparse.ArgumentParser(description="Detect faces using openCV.")
    parser.add_argument("-i", dest="input", required=True, help="input imagine")
    parser.add_argument("-e", dest="encrypt", required=False, action="store_true", help="encrypt imagine")
    parser.add_argument("-d", dest="decrypt", required=False, action="store_true", help="decrypt txt")

    args = parser.parse_args()

    if args.encrypt:
        return DetectFace.encrypt(args.input)
    elif args.decrypt:
        return DetectFace.decrypt(args.input)

    if args.input:
        return detect_faces(args.input)


def _detect_faces(image_path=None, image_buff=None):
    FaceCascade = _face_config()

    assert image_path or image_buff
    if image_path:
        image = cv2.imread(image_path, cv2.CV_LOAD_IMAGE_COLOR)
    else:
        image = cv2.imdecode(np.fromstring(image_buff, dtype=np.uint8), cv2.CV_LOAD_IMAGE_COLOR)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    """
        scaleFactor – Parameter specifying how much the image size is reduced at each image scale.
        minNeighbors – Parameter specifying how many neighbors each candidate rectangle should have to retain it.
        flags – Parameter with the same meaning for an old cascade as in the function cvHaarDetectObjects. It is not used for a new cascade.
        minSize – Minimum possible object size. Objects smaller than that are ignored.
        maxSize – Maximum possible object size. Objects larger than that are ignored.
    """
    faces = FaceCascade.detectMultiScale(
        gray,
        scaleFactor=1.25,
        minNeighbors=5,
        minSize=(45, 45)
        # flags = cv2.CV_HAAR_SCALE_IMAGE
    )

    print(("Found {0} faces!".format(len(faces))))

    for idx, (x, y, w, h) in enumerate(faces):
        # Draw a rectangle around the faces
        # cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 1)

        # trans to 120x120
        crop_img = image[y:y + h, x:x + w]
        resize_crop_img = cv2.resize(crop_img, (120, 120))

        yield idx, resize_crop_img


def _save(file_name, image_buff):
    if isinstance(image_buff, str):
        image = cv2.imdecode(np.fromstring(image_buff, dtype=np.uint8), cv2.CV_LOAD_IMAGE_COLOR)
    else:
        image = image_buff
    return cv2.imwrite(file_name, image)


if __name__ == "__main__":
    main()
