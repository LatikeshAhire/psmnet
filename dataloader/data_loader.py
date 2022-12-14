
import numpy as np
import random
import cv2
import os

import config
import utils
from utils import readPFM
import dataloader.list_file as lt
from PIL import Image


class DataLoaderSceneFlow(object):
    data_path = './dataset/'

    def __init__(self, batch_size, patch_size=(256, 512), max_disp=129, val_size=500):
        self.batch_size = batch_size
        self.patch_size = patch_size
        self.max_disp = max_disp
        self.val_size = val_size
        all_left_img, all_right_img, all_left_disp, \
        test_left_img, test_right_img, test_left_disp = lt.get_sceneflow_img(self.data_path)
        self.data = list(zip(all_left_img, all_right_img, all_left_disp))
        self.train_size = len(all_left_img) - self.val_size
        self.img_height, self.img_width = config.SCENEFLOW_SIZE

    def generator(self, is_training=True):

        train_left = [x[0] for x in self.data[self.val_size:]]
        train_right = [x[1] for x in self.data[self.val_size:]]
        train_labels = [x[2] for x in self.data[self.val_size:]]

        val_left = [x[0] for x in self.data[:self.val_size]]
        val_right = [x[1] for x in self.data[:self.val_size]]
        val_labels = [x[2] for x in self.data[:self.val_size]]

        index = [i for i in range(len(train_labels))]  # 8664*7/8
        random.shuffle(index)
        shuffled_labels = []
        shuffled_left_data = []
        shuffled_right_data = []

        for i in index:
            shuffled_left_data.append(train_left[i])
            shuffled_right_data.append(train_right[i])
            shuffled_labels.append(train_labels[i])
        if is_training:
            for j in range(len(train_labels) // self.batch_size):
                left, right, label = self.load_batch(shuffled_left_data[j * self.batch_size: (j + 1) * self.batch_size],
                                                     shuffled_right_data[
                                                     j * self.batch_size: (j + 1) * self.batch_size],
                                                     shuffled_labels[j * self.batch_size: (j + 1) * self.batch_size],
                                                     is_training)
                left = np.array(left)
                right = np.array(right)
                label = np.array(label)
                yield left, right, label
        else:
            for j in range(self.val_size // self.batch_size):
                left, right, label = self.load_batch(val_left[j * self.batch_size: (j + 1) * self.batch_size],
                                                     val_right[j * self.batch_size: (j + 1) * self.batch_size],
                                                     val_labels[j * self.batch_size: (j + 1) * self.batch_size],
                                                     is_training)
                left = np.array(left)
                right = np.array(right)
                label = np.array(label)
                yield left, right, label

    def load_batch(self, left, right, labels, is_training):
        batch_left = []
        batch_right = []
        batch_label = []
        for x, y, z in zip(left, right, labels):
            # print(x)
            if is_training:
                crop_x = random.randint(0, self.img_height - 1 - self.patch_size[0])
                crop_y = random.randint(0, self.img_width - 1 - self.patch_size[1])
            else:
                crop_x = (self.img_height - 1 - self.patch_size[0]) // 2
                crop_y = (self.img_width - 1 - self.patch_size[1]) // 2

            x = cv2.imread(x)
            assert x.shape[:2] == (self.img_height, self.img_width)
            x = cv2.cvtColor(x, cv2.COLOR_BGR2RGB)
            x = x[crop_x: crop_x + self.patch_size[0], crop_y: crop_y + self.patch_size[1], :]
            x = utils.mean_std(x)
            batch_left.append(x)

            y = cv2.imread(y)
            y = cv2.cvtColor(y, cv2.COLOR_BGR2RGB)
            y = y[crop_x: crop_x + self.patch_size[0], crop_y: crop_y + self.patch_size[1], :]
            y = utils.mean_std(y)
            batch_right.append(y)

            z = readPFM(z)
            # z = cv2.cvtColor(z, cv2.COLOR_BGR2GRAY)
            z = z[crop_x: crop_x + self.patch_size[0], crop_y: crop_y + self.patch_size[1]]
            z[z > (self.max_disp - 1)] = self.max_disp - 1
            batch_label.append(z)
        return batch_left, batch_right, batch_label


class DataLoaderKITTI(object):
    data_path = '/content/psmnet/training/'

    def __init__(self, batch_size, patch_size=[256, 512], max_disp=192,
                 val_size=40):
        self.batch_size = batch_size
        self.patch_size = patch_size
        self.max_disp = max_disp
        self.val_size = val_size
        self.left_data, self.right_data, self.labels = lt.get_kitti_2015_img(self.data_path)
        self.left_data.sort(key=str.lower)
        self.right_data.sort(key=str.lower)
        self.labels.sort(key=str.lower)

        self.train_size = len(self.left_data) - self.val_size
        self.img_height, self.img_width = config.KITTI2015_SIZE

    def generator(self, is_training=True):

        train_left = self.left_data
        train_right = self.right_data
        train_labels = self.labels

        val_left = self.left_data[:self.val_size]
        val_right = self.right_data[:self.val_size]
        val_labels = self.labels[:self.val_size]

        index = [i for i in range(self.train_size)]
        random.shuffle(index)
        shuffled_labels = []
        shuffled_left_data = []
        shuffled_right_data = []

        for i in index:
            shuffled_left_data.append(train_left[i])
            shuffled_right_data.append(train_right[i])
            shuffled_labels.append(train_labels[i])
        if is_training:
            for j in range(self.train_size // self.batch_size):
                left, right, label = self.load_batch(shuffled_left_data[j * self.batch_size: (j + 1) * self.batch_size],
                                                     shuffled_right_data[
                                                     j * self.batch_size: (j + 1) * self.batch_size],
                                                     shuffled_labels[j * self.batch_size: (j + 1) * self.batch_size],
                                                     is_training)
                left = np.array(left)
                right = np.array(right)
                label = np.array(label)
                yield left, right, label
        else:
            for j in range(self.val_size // self.batch_size):
                left, right, label = self.load_batch(val_left[j * self.batch_size: (j + 1) * self.batch_size],
                                                     val_right[j * self.batch_size: (j + 1) * self.batch_size],
                                                     val_labels[j * self.batch_size: (j + 1) * self.batch_size],
                                                     is_training)
                left = np.array(left)
                right = np.array(right)
                label = np.array(label)
                yield left, right, label

    def load_batch(self, left, right, labels, is_training):
        batch_left = []
        batch_right = []
        batch_label = []
        for x, y, z in zip(left, right, labels):
            if is_training:
                crop_x = random.randint(0, self.img_height - self.patch_size[0])
                crop_y = random.randint(0, self.img_width - self.patch_size[1])
            else:
                # self.patch_size = [368, 1232]
                crop_x = (self.img_height - self.patch_size[0]) // 2
                crop_y = (self.img_width - self.patch_size[1]) // 2

            x = cv2.resize(cv2.imread(x), (self.img_width, self.img_height))
            assert x.shape[:2] == (self.img_height, self.img_width)
            x = cv2.cvtColor(x, cv2.COLOR_BGR2RGB)
            x = x[crop_x: crop_x + self.patch_size[0], crop_y: crop_y + self.patch_size[1], :]
            x = utils.mean_std(x)
            batch_left.append(x)

            y = cv2.resize(cv2.imread(y), (self.img_width, self.img_height))
            y = cv2.cvtColor(y, cv2.COLOR_BGR2RGB)
            y = y[crop_x: crop_x + self.patch_size[0], crop_y: crop_y + self.patch_size[1], :]
            y = utils.mean_std(y)
            batch_right.append(y)

            z = Image.open(z)
            z = cv2.resize(np.ascontiguousarray(z, dtype=np.float32) / 256, (self.img_width, self.img_height))

            # z[z > (self.max_disp - 1)] = self.max_disp - 1

            z = z[crop_x: crop_x + self.patch_size[0], crop_y: crop_y + self.patch_size[1]]
            batch_label.append(z)
        return batch_left, batch_right, batch_label


class DataLoaderKITTI_SUBMISSION(object):
    data_path = '/content/psmnet/testing/'

    def __init__(self):
        self.test_left_img, self.test_right_img = lt.get_kitti_2015_submission(self.data_path)

    def generator(self, is_training=False):
        """
        :return:
        """
        for x, y in zip(self.test_left_img, self.test_right_img):
            x = cv2.imread(x)
            x = cv2.cvtColor(x, cv2.COLOR_BGR2RGB)
            x = utils.mean_std(x)

            y = cv2.imread(y)
            y = cv2.cvtColor(y, cv2.COLOR_BGR2RGB)
            y = utils.mean_std(y)

            # pad to (384, 1248)
            top_pad = config.KITTI2015_SIZE[0] - x.shape[0]
            left_pad = config.KITTI2015_SIZE[1] - x.shape[1]
            x = np.lib.pad(x, ((top_pad, 0), (0, left_pad), (0, 0)), mode='constant', constant_values=0)
            y = np.lib.pad(y, ((top_pad, 0), (0, left_pad), (0, 0)), mode='constant', constant_values=0)
            yield np.expand_dims(x, axis=0), np.expand_dims(y, axis=0), None


if __name__ == '__main__':
    # loader = DataLoaderSceneFlow(data_path='../dataset/', batch_size=10, max_disp=192)
    loader = DataLoaderKITTI(batch_size=10, max_disp=192)
