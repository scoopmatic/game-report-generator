# Usage: python ./OpenNMT-py/translate.py -model model.pt -src devel.input -output pred.txt -replace_unk -verbose --max_length 50 -attn_debug > debug.txt
#        python attention_visualization.py --input debug.txt

import sys
import argparse
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np



def read_data(args):

    with open(args.input, "rt", encoding="utf-8") as f:

        preline = ""
        attn_block = False
        data = []

        for line in f:
            line = line.strip()
            if not line:
                preline = ""
                attn_block = False
                continue
            if preline.startswith("PRED SCORE:"):
                attn_block = True
                data.append([])
            if line.startswith("PRED AVG SCORE:"):
                attn_block = False
            if attn_block:
                data[-1].append(line.split())
            preline = line

    return data

def process_data(data):

    processed_data = []

    for sentence in data:
        source, rest = sentence[0], sentence[1:]
        target = [ w[0] for w in rest ]
        weights = [ w[1:] for w in rest ]
        weights = [[float(j.replace("*", "")) for j in i] for i in weights]

        processed_data.append( (source, target, weights) )

    return processed_data



def longest_cont(array):

    longest = [[array[0]]]
    for val in array[1:]:
        if val == longest[-1][-1]+1:
            longest[-1].append(val)
        else:
            longest.append([val])

    return longest


def prune_empty_regions(source, target, weights):

    # dummy solution to remove zero value regions from the heatmap
    # should be rewritten with numpy magic

    weight_array = np.array(weights)

    empty_columns = [] # indices of colums where all rows are close to zero

    for i in range(len(source)): # i is a column index
        is_empty = True
        for j in range(len(target)): # j is a row index
            if weights[j][i] >= 0.05:
                is_empty = False
                break
        if is_empty:
            empty_columns.append(i)

    cont_empty_subseq = longest_cont(empty_columns)

    keep_columns = [i for i in range(len(source)) if i not in empty_columns] # all non empty columns

    for subseq in cont_empty_subseq: # add small empty regions

        if len(subseq) > 10: # prune!!!
            for i in subseq[:3]+subseq[-3:]:
                keep_columns.append(i)
            source[subseq[2]] = source[subseq[2]]+"..."
            source[subseq[-3]] = "..."+source[subseq[-3]]
        else: # keep!!!
            for i in subseq:
                keep_columns.append(i)

    keep_columns.sort()


    a = weight_array[:, keep_columns]
    source_ = [word for i, word in enumerate(source) if i in keep_columns ]


    return source_, target, a


def plot(data, n=5):


    for i, (source, target, weights) in enumerate(data):

        print("source:", source)
        print("prediction:", target)

        source, target, weights = prune_empty_regions(source, target, weights)

        if i >= n:
            break

        fig, ax = plt.subplots(figsize=(16, 5))
        sns.heatmap(weights, vmin=0.0, vmax=1.0, linewidth=0.01, linecolor="black", yticklabels=target, cmap="Reds", ax=ax)
        ax.set_xticks(np.arange(len(source))+0.5)
        ax.axes.set_xticklabels(source, fontsize="x-small", rotation="vertical", ha="center", va="center")
        plt.show()


def main(args):

    data = read_data(args)

    data = process_data(data)

    plot(data, n=100)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', type=str, default='debug.txt', help="")

    args = parser.parse_args()


    main(args)

