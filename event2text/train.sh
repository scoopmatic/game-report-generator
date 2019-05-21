#!/bin/sh

export $(cat config.sh)

MIN_CNT=5
rm -rf data
mkdir data

python $ONMT_PATH/preprocess.py -train_src ../../data-processing/train_input.txt -train_tgt ../../data-processing/train_output.txt -valid_src ../../data-processing/val_input.txt -valid_tgt ../../data-processing/val_output.txt -save_data data/data -src_words_min_frequency $MIN_CNT -tgt_words_min_frequency $MIN_CNT -dynamic_dict 


rm training.log
rm -rf models
mkdir models

# Use Bi-LSTM
LR=0.005
DROP=0.85
VEC=200
BS=192
HID=500

python $ONMT_PATH/train.py -data data/data -save_model models/model -encoder_type brnn -batch_size $BS -train_steps 7000 -valid_steps 100 -save_checkpoint_steps 100 -gpu_ranks 0 -log_file training.log -early_stopping 3 -optim adam -learning_rate $LR -dropout $DROP -word_vec_size $VEC -rnn_size $HID -copy_attn

# Use Transformer
#python ~/arch/OpenNMT-py/train.py -data data/data -save_model models/run4/model -layers 2 -rnn_size 256 -word_vec_size 256 -transformer_ff 256 \
#      -heads 8 -encoder_type transformer -decoder_type transformer -param_init_glorot -batch_size 512 -train_steps 7000 \
#      -valid_steps 100 -save_checkpoint_steps 100 -world_size 2 -gpu_ranks 0 1 -log_file training.log -early_stopping 3 \
#      -position_encoding -max_generator_batches 2 -batch_type tokens -normalization tokens -accum_count 2 \
#        -optim adam -adam_beta2 0.998 -decay_method noam -warmup_steps 8000 -learning_rate 2 -dropout 0.1 \
#        -max_grad_norm 0 -param_init 0  -param_init_glorot \
#        -label_smoothing 0.1

