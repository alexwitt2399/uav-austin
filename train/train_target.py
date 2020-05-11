#!/usr/bin/env python3
""" Script used to train a feature extractor model to differentiate
between all combinations of shape, shape color, alpha, and alpha color. """

import itertools
import pathlib 

import torch 

from third_party.models import efficientnet, resnet 
from data_generation import generate_config as config
from train import datasets

# Get constants from config
NUM_GEN = int(config.NUM_IMAGES)
MAX_SHAPES = int(config.MAX_PER_SHAPE)
FULL_SIZE = config.FULL_SIZE
TARGET_COLORS = config.TARGET_COLORS
ALPHA_COLORS = config.ALPHA_COLORS
COLORS = config.COLORS
CLASSES = config.OD_CLASSES
ALPHAS = config.ALPHAS

a = [
    ["circle"], #config.SHAPE_TYPES,
    TARGET_COLORS,
    config.ALPHAS,
    ALPHA_COLORS,
    [angle for angle in range(0, 360, 45)],
]

def train(model, loader):
    losses = []
    loss_fn = torch.nn.TripletMarginLoss(10)
    optim = torch.optim.SGD(model.parameters(), lr=1e-2)
    for idx, (anchor, positive, negative) in enumerate(loader):
        optim.zero_grad()
        anchor = anchor.cuda()
        positive = positive.cuda()
        negative = negative.cuda()

        out1 = model.final_features(anchor)
        out2 = model.final_features(positive)
        out3 = model.final_features(negative)
        loss = loss_fn(out1, out2, out3)
        losses.append(loss.item())
        print(f"{idx} : {sum(losses) / len(losses)}")
        loss.backward()
        optim.step()

if __name__ == "__main__":
    model = resnet.resnet18(num_classes=len(list(itertools.product(*a))))
    model.cuda()
    classes = {"_".join([str(item) for item in name]) : idx for idx, name in enumerate(set(itertools.product(*a)))}
    dataset = datasets.TargetDataset(
        pathlib.Path("data_generation/data/combinataions_train/images"),
        img_ext=config.IMAGE_EXT,
        img_width=224,
        img_height=224,
        classes=classes,
    )
    loader = torch.utils.data.DataLoader(
        dataset, batch_size=65, pin_memory=True, shuffle=True
    )

    train(model, loader)