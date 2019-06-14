#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from itertools import repeat
import sys
import os
import io
import re

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "OpenNMT-py"))
from onmt.utils.logging import init_logger
from onmt.utils.misc import split_corpus
from onmt.translate.translator import build_translator

import onmt.opts as opts
from onmt.utils.parse import ArgumentParser

length_regex = re.compile("<length>[a-z]+</length>")

def yield_games(f):

    comments = []
    events = []
    for line in f:
        line=line.strip()
        if line.startswith("#"):
            comments.append(line)
            continue
        if not line:
            if events:
                yield comments, events
            events = []
            comments = []
            continue
        # try generating each length
        events.append([re.sub(length_regex, "<length>short</length>", line), re.sub(length_regex, "<length>medium</length>", line), re.sub(length_regex, "<length>long</length>", line)])
    else:
        if events:
            yield comments, events


def detokenize(text):

    text = str(text)
    text = re.sub("</?[a-z]+>", "", text)
    text = re.sub("\*\*[a-z]+\*\*", "", text)
    text = text.replace(' \u2013 ', '\u2013').replace(' ( ', ' (').replace(' ) ', ') ').replace(' , ', ', ').replace(' : ', ':').replace(' — ', '—')
    text = re.sub(r"([0-9])\s-\s([0-9])", r"\1-\2", text) # detokenize times '3 - 5 -osuman'
    text = re.sub(r"([0-9])\s-\s([a-zA-ZÅÄÖåäö\)])", r"\1 -\2", text) # detokenize times '3 - 5 -osuman'
    text = re.sub(r"([a-zA-ZåäöÅÄÖ])\s-\s([a-zA-ZÅÄÖåäö])", r"\1-\2", text) # Juha - Pekka H.
    text = text.replace(" .", ".")
    
    text = " ".join( text.split() )

    return text



def main(opt):
    ArgumentParser.validate_translate_opts(opt)
    logger = init_logger(opt.log_file)

    # make virtual files to collect the predicted output (not actually needed but opennmt still requires this)
    f_output=io.StringIO()

    translator = build_translator(opt, report_score=False, out_file=f_output)

    for i, (comments, game) in enumerate(yield_games(sys.stdin)):
        logger.info("Translating shard %d." % i)

        events = []
        for event_group in game:

            scores, predictions = translator.translate(src=event_group, batch_size=opt.batch_size)

            # PRED SCORE = cumulated log likelihood of the generated sequence

            f_output.truncate(0) # clear this to prevent eating memory
            text_output=[p[0] for p in predictions]
            normalized_scores = [s[0].item()/len(t.split()) for s, t in zip(scores, text_output)]

            max_index = normalized_scores.index(max(normalized_scores))

            events.append( (normalized_scores[max_index], detokenize(text_output[max_index])) )

        for comm in comments:
            print(comm)
        print(" ".join([t for s, t in events]))
        print()


def _get_parser():
    parser = ArgumentParser(description='translate.py')

    opts.config_opts(parser)
    opts.translate_opts(parser)
    return parser


if __name__ == "__main__":
    parser = _get_parser()

    opt = parser.parse_args()
    main(opt)
