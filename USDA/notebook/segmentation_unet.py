# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 22:57:39 2023

@author: richie bao
"""
from segmentation_unet_bool import trainer,task,datamodule


if __name__ == '__main__':
    trainer.fit(model=task,datamodule=datamodule)