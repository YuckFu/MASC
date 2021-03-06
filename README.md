# MASC: Multi-scale Affinity with Sparse Convolution for 3D Instance Segmentation (Technical Report)
## Introduction
This is the PyTorch implementation for our [technical report](https://arxiv.org/abs/1902.04478) which achieves the state-of-the-art performance on the 3D instance segmentation task of the ScanNet benchmark.

## Installation
```
pip install -r requirements.txt
```
We are using Python 3.5.2. And as pointed out by [Issue #3](https://github.com/art-programmer/MASC/issues/3), please consider using Python 3.6 and refer to [SparseConvNet](https://github.com/facebookresearch/SparseConvNet) for related issues.

## Data preparation
To prepare training data from ScanNet mesh models, please run:
```
python train.py --task=prepare --dataFolder=[SCANNET_PATH] --labelFile=[SCANNET_LABEL_FILE_PATH (i.e., scannetv2-labels.combined.tsv)]
```

## Training
To train the main model which predict semantics and affinities, please run:
```
python train.py --restore=0 --dataFolder=[SCANNET_PATH]
```

## Validation
To validate the trained model, please run:
```
python train.py --restore=1 --dataFolder=[SCANNET_PATH] --task=test
```

## Inference
To run the inference using the trained model, please run:

```
python inference.py --dataFolder=[SCANNET_PATH] --task=predict_cluster split=val
```

The task option indicates:
- "predict": predict semantics and affinities
- "cluster": run the clustering algorithm based on the predicted affinities
- "write": write instance segmentation results

The "task" option can contain any combinations of these three tasks, but the earlier task must be run before later tasks. And a task only needs to be run once. The "split" option specifies the data split to run the inference.

## Write results for the final evaluation
To train the instance confidence model, please first generate the instance segmentation results:
```
python inference.py --dataFolder=[SCANNET_PATH] --task=predict_cluster --split=val
python inference.py --dataFolder=[SCANNET_PATH] --task=predict_cluster --split=train
```

Then train the confidence model:
```
python train_confidence.py --restore=0 --dataFolder=[SCANNET_PATH]
```

Predict instance confidence, add additional instances for certain semantic labels, and write instance segmentation results:
```
python inference.py --dataFolder=[SCANNET_PATH] --task=predict_cluster_write split=test
```
