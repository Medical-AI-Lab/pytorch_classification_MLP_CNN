#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import torch
from lib import (
        check_train_options,
        create_model,
        BaseLogger
        )
from lib.component import create_dataloader, print_dataset_info


logger = BaseLogger.get_logger(__name__)


def main(opt):
    breakpoint()
    #params = set_params(opt.args)
    #print_parameters(params)

    epochs = params.train_conf_params.epochs
    save_weight_policy = params.train_conf_params.save_weight_policy
    save_datetime_dir = params.train_conf_params.save_datetime_dir

    dataloaders = {split: create_dataloader(params.dataloader_params, split=split) for split in ['train', 'val']}
    print_dataset_info(dataloaders)

    model = create_model(params.model_params)

    for epoch in range(epochs):
        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()
            elif phase == 'val':
                model.eval()
            else:
                raise ValueError(f"Invalid phase: {phase}.")

            split_dataloader = dataloaders[phase]
            for i, data in enumerate(split_dataloader):
                model.optimizer.zero_grad()
                in_data, labels = model.set_data(data)

                with torch.set_grad_enabled(phase == 'train'):
                    output = model(in_data)
                    model.cal_batch_loss(output, labels)

                    if phase == 'train':
                        model.backward()
                        model.optimize_parameters()

                model.cal_running_loss(batch_size=len(data['imgpath']))

            dataset_size = len(split_dataloader.dataset)
            model.cal_epoch_loss(epoch, phase, dataset_size=dataset_size)

        model.print_epoch_loss(epochs, epoch)

        if model.is_total_val_loss_updated():
            model.store_weight()
            if (epoch > 0) and (save_weight_policy == 'each'):
                model.save_weight(save_datetime_dir, as_best=False)

    model.save_learning_curve(save_datetime_dir)
    model.save_weight(save_datetime_dir, as_best=True)
    if params.model_params.mlp is not None:
        dataloaders['train'].dataset.save_scaler(save_datetime_dir + '/' + 'scaker.pkl')
    params.save_parameter(save_datetime_dir)


if __name__ == '__main__':
    try:
        datetime_name = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        logger.info(f"\nTraining started at {datetime_name}.\n")

        opt = check_train_options(datetime_name)
        breakpoint()

        main(opt)

    except Exception as e:
        logger.error(e, exc_info=True)

    else:
        logger.info('\nTraining finished.\n')
