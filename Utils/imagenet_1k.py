import csv
from pathlib import Path
from collections import defaultdict

import torch

from robustbench.loaders import default_loader


class ImageNet1K(torch.utils.data.Dataset):
    def __init__(self, dataset_root=None, transform=None, target_transform=None):
        if dataset_root == None:
          raise ValueError("Dataset root is None!")
        self.img_paths, self.img_labels, self.img_target_labels = self._load_imagenet_1000(dataset_root)
        self.transform = transform
        self.target_transform = target_transform
        self.loader = default_loader

    def _load_imagenet_1000(self, dataset_root):
      """
      Dataset downoaded form kaggle
      https://www.kaggle.com/datasets/google-brain/nips-2017-adversarial-learning-development-set
      Resized from 299x299 to 224x224
      Args:
          dataset_root (str): root folder of dataset
      Returns:
          img_paths (list of strs): the paths of images
          gt_labels (list of ints): the ground truth label of images
          tgt_labels (list of ints): the target label of images

      source: https://github.com/rmura498/Surrogate_ensemble/blob/main/Utils/load_models.py
      """
      dataset_root = Path(dataset_root)
      img_paths = list(sorted(dataset_root.glob('*.png')))
      gt_dict = defaultdict(int)
      tgt_dict = defaultdict(int)
      with open(str(dataset_root) + '/' + "images.csv", newline='') as csvfile:
          reader = csv.DictReader(csvfile)
          for row in reader:
              gt_dict[row['ImageId']] = int(row['TrueLabel'])
              tgt_dict[row['ImageId']] = int(row['TargetClass'])
      gt_labels = [gt_dict[key] - 1 for key in sorted(gt_dict)]  # zero indexed
      tgt_labels = [tgt_dict[key] - 1 for key in sorted(tgt_dict)]  # zero indexed
      return img_paths, gt_labels, tgt_labels

    def __len__(self):
        return len(self.img_labels)

    def __getitem__(self, idx):
        img_path = self.img_paths[idx]
        # image = read_image(str(img_path), mode=ImageReadMode.RGB)
        # image = Image.open(str(img_path)).convert('RGB')
        image = self.loader(str(img_path))
        label = torch.tensor([self.img_labels[idx]])
        if self.transform:
            image = self.transform(image)
        if self.target_transform:
            label = self.target_transform(label)
        return image, label
