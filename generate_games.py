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

    events = []
    for line in f:
        line=line.strip()
        if not line:
            if events:
                yield events
            events = []
            continue
        # try generating each length
        events.append([re.sub(length_regex, "<length>short</length>", line), re.sub(length_regex, "<length>medium</length>", line), re.sub(length_regex, "<length>long</length>", line)])
    else:
        if events:
            yield events



def main(opt):
    ArgumentParser.validate_translate_opts(opt)
    logger = init_logger(opt.log_file)

    # make virtual files to collect the predicted output (not actually needed but opennmt still requires this)
    f_output=io.StringIO()

    translator = build_translator(opt, report_score=False, out_file=f_output)

    for i, game in enumerate(yield_games(sys.stdin)):
        logger.info("Translating shard %d." % i)

        events = []
        for event_group in game:

            scores, predictions = translator.translate(src=event_group, batch_size=opt.batch_size)

            # PRED SCORE = cumulated log likelihood of the generated sequence

            f_output.truncate(0) # clear this to prevent eating memory
            text_output=[p[0] for p in predictions]
            normalized_scores = [s[0].item()/len(t.split()) for s, t in zip(scores, text_output)]

            max_index = normalized_scores.index(max(normalized_scores))

            events.append( (normalized_scores[max_index], text_output[max_index]) )

        for s, t in events:
            print(t)
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
