#!/bin/bash
python wa_sgd_opt_outplace.py --classes 10 -b 128 --ave-weight --lr 0.01 --sgd SGDOPO_MW --momentum 0.0
python main.py -a vgg16 --multiprocessing-distributed --world-size 1 --rank 0 -b 128 --workers 8 --lr 0.01 --momentum 0.0 --classes 10 /home/gw/data/imagenet_10
#python wa_sgd_opt_outplace.py --classes 10 -b 128 --ave-weight --lr 0.01 --sgd SGDOPO
#python wa_sgd_opt_outplace.py --classes 10 -b 128 --ave-weight --lr 0.01 --sgd SGDOPO_W
#python wa_sgd_opt_outplace.py --classes 10 -b 128 --ave-weight --lr 0.01
#python wa_sgd_opt_outplace.py --classes 10 -b 128 --ave-weight --lr 0.01
#python wa_sgd.py --classes 10 -b 128 --ave-weight --lr 0.01
#python main.py -a vgg16 --multiprocessing-distributed --world-size 1 --rank 0 -b 128 --workers 8 --lr 0.01 --classes 10 /home/gw/data/imagenet_10
#python wa_sgd.py --classes 10 -b 256 --lr 0.1 | tee ./logs/res50_ave_g_adjlr01_m09.log
