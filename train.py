#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import torch
from lib import (
        set_options,
        create_model,
        print_paramater,
        save_parameter,
        BaseLogger
        )
from lib.component import create_dataloader, print_dataset_info


logger = BaseLogger.get_logger(__name__)


def main(args):
    model = create_model(args.model_params)
    dataloaders = {split: create_dataloader(args.dataloader_params, split=split) for split in ['train', 'val']}

    print_paramater(args.print_params, phase='train')
    print_dataset_info(dataloaders)

    epochs = args.conf_params.epochs
    save_weight_policy = args.conf_params.save_weight_policy
    save_datetime_dir = args.conf_params.save_datetime_dir

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

    if args.model_params.mlp is not None:
        dataloaders['train'].dataset.save_scaler(save_datetime_dir + '/' + 'scaler.pkl')

    save_parameter(args.save_params, save_datetime_dir + '/' + 'parameters.json')


if __name__ == '__main__':
    try:
        datetime_name = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        logger.info(f"\nTraining started at {datetime_name}.\n")

        args = set_options(datetime_name=datetime_name, phase='train')
        main(args)

    except Exception as e:
        logger.error(e, exc_info=True)

    else:
        logger.info('\nTraining finished.\n')
