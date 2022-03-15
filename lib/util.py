#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from logging.handlers import RotatingFileHandler
import sys
import os
import glob
import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch

class NervusLogger:
    _unexecuted_configure = True

    @classmethod
    def get_logger(cls, filename, result_output=False):
        if cls._unexecuted_configure:
            cls._init_logger()

        logger = logging.getLogger('nervus.{}'.format(filename))

        if result_output:
            cls._set_result_output_handler(logger, filename)

        return logger

    @classmethod
    def _set_result_output_handler(cls, logger:logging.Logger, filename):
        _today_str = datetime.date.today().strftime("%Y%m%d")
        _results_dir = Path(__file__).parents[1].joinpath('results', _today_str)
        if not _results_dir.exists():
            _results_dir.mkdir(parents=True)
        _filename = filename.split('.')[-1]
        _path = _results_dir.joinpath(_filename).with_suffix('.log')
        fh = RotatingFileHandler(_path, maxBytes=102400)
        fh.setLevel(logging.INFO)
        fh.addFilter(lambda log_record: log_record.levelno == logging.INFO)
        logger.addHandler(fh)

    @classmethod
    def set_level(cls, level):
        _nervus_root_logger = logging.getLogger('nervus')
        _nervus_root_logger.setLevel(level)

    @classmethod
    def _init_logger(cls):
        _nervus_root_logger = logging.getLogger('nervus')
        _nervus_root_logger.setLevel(logging.INFO)

        ## error log
        _logs_path = Path(__file__).parents[1].joinpath('logs', 'error.log')
        fh = RotatingFileHandler(_logs_path, maxBytes=102400)
        fh.setLevel(logging.WARNING)
        fh_format = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
        fh.setFormatter(fh_format)
        _nervus_root_logger.addHandler(fh)

        ## uppper warining
        sh = logging.StreamHandler()
        sh.setLevel(logging.WARNING)
        sh_format = logging.Formatter('%(levelname)-8s %(message)s')
        sh.setFormatter(sh_format)
        _nervus_root_logger.addHandler(sh)

        ## lower warning
        sh_info = logging.StreamHandler()
        sh_info.setLevel(logging.DEBUG)
        sh_info.addFilter(lambda log_record: log_record.levelno < logging.WARNING)
        _nervus_root_logger.addHandler(sh_info)

        cls._unexecuted_configure = False

logger = NervusLogger.get_logger('lib.util')

# Even if GPU available, set CPU as device when specifying CPU.
def set_device(gpu_ids):
    if gpu_ids:
        assert torch.cuda.is_available(), 'No avalibale GPU on this machine. Use CPU.'
        primary_gpu_id = gpu_ids[0]
        device_name = f'cuda:{primary_gpu_id}'
        device = torch.device(device_name)
    else:
        device = torch.device('cpu')
    return device


def get_column_value(df, column_name:str, value_list:list):
    assert (value_list!=[]), 'The list of values is empty list.' #  ie. When value_list==[], raise AssertionError.
    df_result = pd.DataFrame([])
    for value in value_list:
        df_tmp = df[df[column_name] == value]
        df_result = pd.concat([df_result, df_tmp], ignore_index=True)
    return df_result


def get_target(source_dir, target):
    if (target is None):
        dirs = glob.glob(source_dir + '/*')
        if dirs:
            target_dir = sorted(dirs, key=lambda f: os.stat(f).st_mtime, reverse=True)[0]   # latest
        else:
            target_dir = None
            logger.error(f"No directory in {source_dir}")
    else:
        target_dir = os.path.join(source_dir, target)
        if os.path.isdir(target_dir):
            target_dir = target_dir
        else:
            target_dir = None
            logger.error(f"No such a directory: {target_dir}")
    return target_dir


def read_train_parameters(parameters_path):
    df_parameters = pd.read_csv(parameters_path, index_col=0)
    df_parameters = df_parameters.fillna(np.nan).replace([np.nan],[None])
    parameters_dict = df_parameters.to_dict()['value']
    return parameters_dict


def str2int(gpu_ids_str:str):
    gpu_ids_str = gpu_ids_str.replace('[', '').replace(']', '')
    if gpu_ids_str == '':
        gpu_ids = []
    else:
        gpu_ids = gpu_ids_str.split(',')
        gpu_ids = [ int(i) for i in gpu_ids ]
    return gpu_ids


def update_summary(summary_dir, summary,  df_summary_new):
    summary_path = os.path.join(summary_dir, summary)
    if os.path.isfile(summary_path):
        df_summary = pd.read_csv(summary_path, dtype=str)
        df_summary_updated = pd.concat([df_summary, df_summary_new], axis=0)
    else:
        os.makedirs(summary_dir, exist_ok=True)
        df_summary_updated = df_summary_new
    df_summary_updated.to_csv(summary_path, index=False)

