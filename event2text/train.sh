#!/bin/bash

data="data"
model="model"
inmax=350
outmax=50

mkdir $model
rm $model/*

mkdir $data
rm $data/prep*

cat $data/train.all | cut -f 1 > $data/train.input
cat $data/train.all | cut -f 2 > $data/train.output

cat $data/devel.all | cut -f 1 > $data/devel.input
cat $data/devel.all | cut -f 2 > $data/devel.output

cat $data/test.all | cut -f 1 > $data/test.input
cat $data/test.all | cut -f 2 > $data/test.output


python OpenNMT-py/preprocess.py -train_src $data/train.input -train_tgt $data/train.output -valid_src $data/devel.input -valid_tgt $data/devel.output -save_data $data/prep -src_words_min_frequency 2 -tgt_words_min_frequency 2 -dynamic_dict --src_seq_length $inmax --tgt_seq_length $outmax

python OpenNMT-py/train.py -data $data/prep -save_model $model/model -encoder_type brnn -train_steps 8000 -valid_steps 500 -save_checkpoint_steps 500 -log_file training.log -early_stopping 3 -gpu_ranks 0 -optim adam -learning_rate 0.0005 -layers 2 -batch_size 32 -copy_attn -reuse_copy_attn -coverage_attn

# Evaluate
rm eval.txt
# Simple detokenization of game scores to deflate BLEU scores
cat $data/devel.output | sed "s/ – /–/g" |sed "s/ - /-/g" | sed "s/ — /—/g" | sed "s/( /(/g" | sed "s/ )/)/g" > $data/devel.output.detok
for i in {500..8000..500} ;
do
echo "Evaluating step $i"
python OpenNMT-py/translate.py -gpu 0 -model $model/model_step_$i.pt -src $data/devel.input -output pred.txt -replace_unk -max_length 50
cat pred.txt | sed "s/ – /–/g" |sed "s/ - /-/g" | sed "s/ — /—/g" | sed "s/( /(/g" | sed "s/ )/)/g" > pred.txt.detok
BLEU=$(perl OpenNMT-py/tools/multi-bleu.perl $data/devel.output.detok < pred.txt.detok)
echo $BLEU $i >> eval.txt
echo $BLEU
done

BEST="$model/model_step_$(cat eval.txt | cut -d" " -f3,9|sort -n|tail -1|cut -d" " -f2).pt"
echo "Best model: $BEST"
cp -v $BEST trained_model.pt

# Test
cat $data/test.output | sed "s/ – /–/g" |sed "s/ - /-/g" | sed "s/ — /—/g" | sed "s/( /(/g" | sed "s/ )/)/g" > $data/test.output.detok
python OpenNMT-py/translate.py -gpu 0 -model $BEST -src $data/test.input -output test_pred.txt -replace_unk -max_length 50
cat test_pred.txt | sed "s/ – /–/g" |sed "s/ - /-/g" | sed "s/ — /—/g" | sed "s/( /(/g" | sed "s/ )/)/g" > test_pred.txt.detok
BLEU=$(perl OpenNMT-py/tools/multi-bleu.perl $data/test.output < test_pred.txt)
echo "Performance on test set: $BLEU"
BLEU_DETOK=$(perl OpenNMT-py/tools/multi-bleu.perl $data/test.output.detok < test_pred.txt.detok)
echo "Performance on test set, detokenized: $BLEU_DETOK"
