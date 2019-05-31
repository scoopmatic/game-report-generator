import rbfopt
import os
import sys
import numpy as np
import argparse
import re
import os
import glob

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "OpenNMT-py"))

bleu_regex=re.compile("BLEU = ([0-9\.]+)")

# global data parameters
train_dir=None
model_dir=None
logging_fname=None
max_seq_len=None

def round_even(x):
    if x%2==0:
        return x
    else:
        return round(x/2)*2


def train(params):

    # preprocess
    os.system("python ./OpenNMT-py/preprocess.py -train_src {data}/ready/train.input -train_tgt {data}/ready/train.output -valid_src {data}/ready/devel.input -valid_tgt {data}/ready/devel.output -save_data {model}/demo -src_words_min_frequency 2 -tgt_words_min_frequency 2 -dynamic_dict --src_seq_length {maxl} --tgt_seq_length {maxl}".format(data=train_dir, model=model_dir, maxl=max_seq_len))

    os.system("python ./OpenNMT-py/train.py -data {model}/demo -save_model {model}/demo-model -encoder_type brnn -train_steps 8000 -valid_steps 500 -save_checkpoint_steps 500 -gpu_ranks 0 -optim adam {p}".format(model=model_dir, p=params))


def evaluate():

    max_score = 0.0
    steps = None

    for i in range(500, 8500, 500):
        os.system("python ./OpenNMT-py/translate.py -gpu 0 -model {model}/demo-model_step_{idx}.pt -src {data}/ready/devel.input -output {model}/pred.txt -replace_unk -max_length {maxl}".format(data=train_dir, model=model_dir, idx=i, maxl=max_seq_len))
        os.system("perl OpenNMT-py/tools/multi-bleu.perl {data}/ready/devel.output < {model}/pred.txt > {model}/bleu.txt".format(data=train_dir, model=model_dir, maxl=max_seq_len))

        with open("{model}/bleu.txt".format(model=model_dir), "rt", encoding="utf-8") as f:
            data=f.readline().strip()
        if not re.match(bleu_regex, data):
            continue
        score = float(re.match(bleu_regex, data).group(1))
        if score > max_score:
            max_score = score
            steps = i

    return max_score, steps


def my_black_box(params):


    print(train_dir,model_dir,logging_fname)

    

#    treebank="ga_idt"
#    os.system("rm lemmatizer_models_v2.2/{x}_optimizer/model_acc*".format(x=treebank))


    # parameters
    (word_emb, rnn_size, dropout, lr, rnn_layers, copy_attn, coverage_attn, batch_size)=params
    
    # even numbers
    word_emb=round_even(word_emb)
    rnn_size=round_even(rnn_size)

    params_string = "--word_vec_size {} --rnn_size {} --dropout {} --learning_rate {} --layers {} --batch_size {}".format(int(word_emb), int(rnn_size), dropout, lr, int(rnn_layers), int(batch_size))

    if copy_attn == 1:
        params_string += " --copy_attn --reuse_copy_attn"

    if coverage_attn == 1:
        params_string += " --coverage_attn"


    train(params_string)
    max_valid_bleu, steps = evaluate()

    with open(logging_fname, "at", encoding="utf-8") as logging_file:
        print(int(word_emb), int(rnn_size), dropout, lr, int(rnn_layers), int(copy_attn), int(coverage_attn), int(batch_size), max_valid_bleu, steps, sep="\t", file=logging_file)

    return 100-max_valid_bleu

    

#    min_valid_loss=callable(["filler", "-data", "lemmatizer_models_v2.2/{x}_optimizer/model".format(x=treebank), "-save_model", "lemmatizer_models_v2.2/{x}_optimizer/model".format(x=treebank), "-encoder_type", "brnn", "-gpuid", "0","-optim", "adam", "-epochs", "15", "-start_decay_at", "8", "-word_vec_size", str(int(char_emb)), "-rnn_size", str(int(rnn_size)), "-dropout", str(drop), "-learning_rate", str(lr), "-learning_rate_decay", str(lr_decay)])

#    print(char_emb, rnn_size, drop, lr, lr_decay, min_valid_loss, sep="\t", file=logging_file)
#    logging_file.close()
#    return min_valid_loss


def main(args):

    # example: bb = rbfopt.RbfoptUserBlackBox(3, np.array([0] * 3), np.array([10] * 3), np.array(['R', 'I', 'R']), obj_funct)

    # data (hacky, no time to define properly right now)
    global train_dir, model_dir, logging_fname, max_seq_len
    if args.mode == "single":
        train_dir = "training_data_single"
        model_dir = "hockey_model_single"
        logging_fname = "optimizer.logging.single"
        max_seq_len = 50
    elif args.mode == "combined_events":
        train_dir = "training_data_combined_events"
        model_dir = "hockey_model_combined_events"
        logging_fname = "optimizer.logging.combined_events"
        max_seq_len = 50
    elif args.mode == "full_report":
        train_dir = "training_data_full_report"
        model_dir = "hockey_model_full_report"
        logging_fname = "optimizer.logging.full_report"
        max_seq_len = 300
    else:
        print("Unknown mode:", mode, file=sys.stderr)
        sys.exit()

    if os.path.exists(logging_fname):
        os.remove(logging_fname)

    files = glob.glob(model_dir+"/*")
    for _f in files:
        os.remove(_f)

    # list of parameters:

    # word embeddings (50-700)      --word_vec_size
    # recurrent size (300-1000)     --rnn_size
    # dropout (0.0-0.6)             --dropout
    # learning_rate (0.0001-0.01)   --learning_rate
    # enc/dec layers (1-3)          --layers
    # copy attention layer (1/0)    --copy_attn --reuse_copy_attn
    # coverage attention layer (1/0)--coverage_attn
    # batch size (16/64)            --batch_size
    # --train_steps


                                           # emb  rnn  drop   lr     layers  copy  cover batch
    bb=rbfopt.RbfoptUserBlackBox(8,np.array([50,  300,  0.0, 0.00001, 1,      0,    0,    16]),\
                                   np.array([700, 1000, 0.6, 0.01,    3,      1,    1,    64]),np.array(['I','I','R','R','I','I','I','I']), my_black_box)

    settings = rbfopt.RbfoptSettings(max_clock_time=36*60*60*1,target_objval=0.0,num_cpus=1,minlp_solver_path='/home/jmnybl/optimizer_tools/bonmin', nlp_solver_path='/home/jmnybl/optimizer_tools/Ipopt-3.7.1-linux-x86_64-gcc4.3.2/bin/ipopt')

    alg = rbfopt.RbfoptAlgorithm(settings, bb)
    val, x, itercount, evalcount, fast_evalcount = alg.optimize()



if __name__=="__main__":

    argparser = argparse.ArgumentParser(description='Optimizer for the generation model')
    argparser.add_argument('--mode', choices=['single', 'full_report', 'combined_events'], default= "single", help='')
    args = argparser.parse_args()

    main(args)




