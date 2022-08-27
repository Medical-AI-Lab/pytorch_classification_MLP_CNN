#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
import numpy as np
import pandas as pd

from sklearn import metrics
from sklearn.preprocessing import label_binarize
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors

sys.path.append((Path().resolve() / '../').name)
from logger.logger import Logger


logger = Logger.get_logger('metrics.yy')


class Metrics:
    def __init__(self):
        self.y_obs = None
        self.y_pred = None
        self.r2 = None

    def set_values(self, y_obs, y_pred):
        self.y_obs = y_obs.values
        self.y_pred = y_pred.values
        self.r2 = metrics.r2_score(y_obs, y_pred)


class LabelMetrics:
    def __init__(self):
        self.val = Metrics()
        self.test = Metrics()

    def cal_label_metrics(self, raw_label_name, df_label):
        for split in ['val', 'test']:
            df_split = df_label.query('split == @split')
            y_obs = df_split[raw_label_name]
            y_pred = df_split['pred_' + raw_label_name]
            if split == 'val':
                self.val.set_values(y_obs, y_pred)
            elif split == 'test':
                self.test.set_values(y_obs, y_pred)
            else:
                logger.error('Invalid split.')
                exit()


def cal_inst_metrics(df_inst):
    raw_label_list = list(df_inst.columns[df_inst.columns.str.startswith('label')])
    inst_metrics = dict()
    for raw_label_name in raw_label_list:
        required_columns = list(df_inst.columns[df_inst.columns.str.contains(raw_label_name)]) + ['split']
        df_label = df_inst[required_columns]
        label_metrics = LabelMetrics()
        label_metrics.cal_label_metrics(raw_label_name, df_label)
        inst_metrics[raw_label_name] = label_metrics
    return inst_metrics


def cal_metrics(likelihood_path):
    df_likelihood = pd.read_csv(likelihood_path)
    whole_metrics = dict()
    for inst in df_likelihood['Institution'].unique():
        df_inst = df_likelihood.query('Institution == @inst')
        whole_metrics[inst] = cal_inst_metrics(df_inst)
    return whole_metrics


def plot_inst_yy(inst, inst_metrics):
    raw_label_list = inst_metrics.keys()
    num_splits = len(['val', 'test'])
    num_rows = 1
    num_cols = len(raw_label_list) * num_splits
    base_size = 7
    height = num_rows * base_size
    width = num_cols * height
    fig = plt.figure(figsize=(width, height))

    for i, raw_label_name in enumerate(raw_label_list):
        label_metrics = inst_metrics[raw_label_name]
        val_offset = (i * num_splits) + 1
        test_offset = val_offset + 1

        val_ax = fig.add_subplot(
                                num_rows,
                                num_cols,
                                val_offset,
                                title=inst + ': ' + raw_label_name + '\n' + 'val: Observed-Predicted Plot',
                                xlabel='Observed',
                                ylabel='Predicted',
                                xmargin=0,
                                ymargin=0
                                )
        test_ax = fig.add_subplot(
                                num_rows,
                                num_cols,
                                test_offset,
                                title=inst + ': ' + raw_label_name + '\n' + 'test: Observed-Predicted Plot',
                                xlabel='Observed',
                                ylabel='Predicted',
                                xmargin=0,
                                ymargin=0
                                )

        y_obs_val = label_metrics.val.y_obs
        y_pred_val = label_metrics.val.y_pred
        y_obs_test = label_metrics.test.y_obs
        y_pred_test = label_metrics.test.y_pred

        y_values_val = np.concatenate([y_obs_val.flatten(), y_pred_val.flatten()])
        y_values_test = np.concatenate([y_obs_test.flatten(), y_pred_test.flatten()])

        y_values_val_min, y_values_val_max, y_values_val_range = np.amin(y_values_val), np.amax(y_values_val), np.ptp(y_values_val)
        y_values_test_min, y_values_test_max, y_values_test_range = np.amin(y_values_test), np.amax(y_values_test), np.ptp(y_values_test)

        # Plot
        color = mcolors.TABLEAU_COLORS
        val_ax.scatter(y_obs_val, y_pred_val, color=color['tab:blue'], label='val')
        test_ax.scatter(y_obs_test, y_pred_test, color=color['tab:orange'], label='test')

        # Draw diagonal line
        val_ax.plot([y_values_val_min - (y_values_val_range * 0.01), y_values_val_max + (y_values_val_range * 0.01)],
                    [y_values_val_min - (y_values_val_range * 0.01), y_values_val_max + (y_values_val_range * 0.01)], color='red')

        test_ax.plot([y_values_test_min - (y_values_test_range * 0.01), y_values_test_max + (y_values_test_range * 0.01)],
                     [y_values_test_min - (y_values_test_range * 0.01), y_values_test_max + (y_values_test_range * 0.01)], color='red')

    fig.tight_layout()
    return fig


def save_yy(whole_metrics, datetime, likelihood_path):
    for inst, inst_roc in whole_metrics.items():
        fig = plot_inst_yy(inst, inst_roc)
        save_dir = Path('./results/sets', datetime, 'yy')
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = Path(save_dir, inst + '_yy_' + likelihood_path.stem.replace('likelihood_', '') + '.png')  # 'likelihood_weight_epoch-010_best.csv'  -> inst_yy_weight_epoch-010_best.png
        fig.savefig(save_path)
        plt.close()


def make_summary(whole_metrics, datetime, likelihood_path):
    df_summary = pd.DataFrame()
    for inst, inst_metrics in whole_metrics.items():
        _new = dict()
        _new['datetime'] = [datetime]
        _new['weight'] = [likelihood_path.name.replace('likelihood_', '')]
        _new['Institution'] = [inst]
        for raw_label_name, label_metrics in inst_metrics.items():
            _new[raw_label_name + '_val_r2'] = [f"{label_metrics.val.r2:.2f}"]
            _new[raw_label_name + '_test_r2'] = [f"{label_metrics.test.r2:.2f}"]
        df_summary = pd.concat([df_summary, pd.DataFrame(_new)], ignore_index=True)

    df_summary = df_summary.sort_values('Institution')
    return df_summary


def print_metrics(df_summary):
    label_list = list(df_summary.columns[df_summary.columns.str.startswith('label')])
    num_splits = len(['val', 'test'])
    _column_list = [label_list[i:i+num_splits] for i in range(0, len(label_list), num_splits)]
    for _, row in df_summary.iterrows():
        logger.info(row['Institution'])
        for _column in _column_list:
            label_name = _column[0].replace('_val_r2', '')
            logger.info(f"{label_name:<25} val_r2: {row[_column[0]]:>7}, test_r2: {row[_column[1]]:>7}")


def make_yy(datetime, likelihood_path):
    whole_metrics = cal_metrics(likelihood_path)
    save_yy(whole_metrics, datetime, likelihood_path)
    df_summary = make_summary(whole_metrics, datetime, likelihood_path)
    print_metrics(df_summary)
    return df_summary
