from util_misc import AttrDict
import os
from torchgeo.datamodules import NAIPChesapeakeDataModule
from pytorch_lightning.callbacks import EarlyStopping, ModelCheckpoint
from pytorch_lightning.loggers import CSVLogger
import pytorch_lightning as pl
from torchgeo.trainers import SemanticSegmentationTask
from multiprocessing import freeze_support
from pytorch_lightning.callbacks import TQDMProgressBar

__C=AttrDict() 
args=__C

__C.data=AttrDict()
__C.data.Chesapeake_root=r'E:\data\Delaware'
__C.data.Chesapeake_LC=os.path.join(args.data.Chesapeake_root,'LC')
__C.data.Chesapeake_imagery=os.path.join(args.data.Chesapeake_root,'imagery')
__C.data.naip_de_entityID='./data/naip_Delaware/naip_63b945b372d740b7.shp'

__C.training=AttrDict()
#__C.training.dirpath=r'E:\model\segmentation_unet'
__C.training.dirpath=r'C:\Users\richi\omen_richiebao\omen_temp\segmentation_unet'

datamodule=NAIPChesapeakeDataModule(naip_root_dir=args.data.Chesapeake_imagery,
                                    chesapeake_root_dir=args.data.Chesapeake_LC,
                                    batch_size=1,
                                    #num_workers=6,
                                    patch_size=1024,
                                   )

task=SemanticSegmentationTask(
    segmentation_model='unet',
    encoder_name='resnet34',
    encoder_weights='imagenet',
    pretrained=True,
    in_channels=4,
    num_classes=13,
    ignore_index=-1000,
    loss='ce',
    learning_rate=0.1,
    learning_rate_schedule_patience=5,
    ignore_zeros=True,
    )

experiment_dir=args.training.dirpath
checkpoint_callback=ModelCheckpoint(monitor="val_loss", dirpath=experiment_dir, save_top_k=1, save_last=True)
early_stopping_callback=EarlyStopping(monitor="val_loss", min_delta=0.00, patience=10)
csv_logger=CSVLogger(save_dir=experiment_dir, name="segmentation_unet")


in_tests="PYTEST_CURRENT_TEST" in os.environ

trainer=pl.Trainer(
    callbacks=[checkpoint_callback,early_stopping_callback],
    # callbacks=[TQDMProgressBar(refresh_rate=10)],
    logger=[csv_logger],
    default_root_dir=experiment_dir,
    min_epochs=1,
    max_epochs=10,
    fast_dev_run=in_tests,
    accelerator="gpu",    
)

if __name__ == '__main__':
    trainer.fit(model=task,datamodule=datamodule)