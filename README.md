# Nervus
This is an AI model used for single/multi-label and/or single/multi-class tasks with image and/or tabular data.
Although this has a possibility to apply wide range of fields, we intended to use this model for medical imaging classification task.

Additionally, we merged DeepSurv model [citation] into this model, which is a model that merges Cox proportional hazard model with deep learning. It is a useful model for prognosis estimation by dealing with binary variables such as decease or not, and the period until the event. The original DeepSurv model could only handle tabular data, but we have added images to it.  

Nervus can handle the following task:
- Single/Multi-label-output classification with any of MLP, CNN, or MLP+CNN.
- Single/Multi-label-output regression with any of MLP, CNN, or MLP+CNN.
- DeepSurv with any of MLP, CNN, or MLP+CNN.

# Brief Usage
- Directory tree  
Set directories as follows.  

┌Nervus (this repository)  
└materials   
　　└images (this repository has image files for CNN.)  
　　└splits  
　　　　 └trials.csv (any name is available if you change `parameters/parameters.csv`)

- Brief modification for your task
  - parameters/parameters.csv  
    CSV must contain columns named `id_XXX`, `filepath`, `label_XXX`, and `split`.  
    Detailed explanation is shown in below.
  - work_all.sh  
    Change `gpu_ids` depending on how many GPUs you can use. Default is "-1" which means to use CPU only.

- To work and evaluate  
`$bash work_all.sh`

See Google Colab codes.  
https://colab.research.google.com/drive/1vpP-veRHPnTEwzDOzRZ0cXcHHY0u7-oJ

# Detailed Preparation
## CSV
This is the csv which we show as trials.csv in the brief usage section.  
CSV must contain columns named `id_XXX`, `filepath`, `label_XXX`, and `split`.

Examples:
| id_uniq | filepath | label_cancer | split |
| -----| ----------- | --------- | ----- |
| 0001 | png_128/AAA.png | malignant | train |
| 0002 | png_128/BBB.png | benign | val |
| 0003 | png_128/CCC.png | malignant | train |
| 0004 | png_128/DDD.png | malignant | test |
| 0005 | png_128/EEE.png | benign | train |
| 0006 | png_128/FFF.png | malignant | train |
| 0007 | png_128/GGG.png | benign | train |
| 0008 | png_128/HHH.png | benign | val |
| 0009 | png_128/III.png | malignant | test |
| :  | : | : | : |

Note `id_XXX` must be unique.
`filepath` should have a path to images for the model.
`label_XXX` should have a classification target. Any name is available. If you use more than two `label_XXX`, it will be automatically recognize multi-label classification and automatically prepare a proper number of classifiers (FCs). 
`split` should have `train`, `val`, and `test`.
When you use inputs other than image, `input_XXX` is needed. 
When you use deepsurv, `periords_XXX` is needed as well.

## Model development
For training, validation, and testing, `parameter.csv` and `work_all.sh` should be modified.

GPU and path to `parameter.csv` should be defined in the `work_all.sh`.
Other parameters are defined in the `parameter.csv`. 

### parameter.csv items
- task: task name
  - example: classification, regression, deepsurv
- csv_name: csv file name contains labeled training data, validation data, and test data
  - default path: ../materials/splits/ (see: align_env.py)
- image_dir: image dataset directory name
  - default path: ../materials/images/ (see: align_env.py)
- model: model name
  - example
    - MLP only: MLP
    - CNN only: B0, B2, B4, B6, ResNet, ResNet18, DenseNet, ConvNeXtTiny, ConvNeXtSmall, ConvNeXtBase, and ConvNeXtLarge.
    - MLP+CNN : MLP+B0, MLP+ResNet, ... (combine above)
- criterion: Loss function
  - example: 
    - classification: CEL ※CEL=CrossEntropyLoss
    - regression: MSE, RMSE, MAE
    - deepsurv: NLL
- optimizer: optimization algorithm
  - example: SGD, Adadelta, Adam, RMSprop
- epochs: number of training with entire dataset 
- bach_size: number of training data in each batch
- sampler: samples elements randomly or not.
  - example: yes, no
- augmentation: increase the amount of data by slightly modified copies or created synthetic.
  - example: yes, no

# Task
## Single-label/Multi-label output classification, regression, or deepsurv.
For all task, `train.py` and `test.py` are used. And also, `evaluation/roc.py`, `evaluation/yy.py` or `evaluation/c_index.py` are used depending on task.

# Only for test
Use `python test.py --test_datetime yy-mm-dd-HH-MM-SS`.


# Debugging
## MakeFile
Edit Makefile according to task.

## env
`~/lib/align_env.py`

## Logger
NervusLogger
only to configure logger, usage is the same with default logging module. see [here](https://docs.python.org/3/howto/logging.html).  
The default level is INFO, and handler is StreamHandler.
```py
logger = NervusLogger.get_logger('logger_name')
...
logger.info('info message')
logger.error('error message')
```
when debug. call set_level method.
```py
logger = NervusLogger.get_logger('logger_name')
NervusLogger.set_level(logging.DEBUG)
...
logger.debug('debug message')
```
# CUDA VERSION
CUDA Version = 11.3, 11.4
