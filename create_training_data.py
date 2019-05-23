import json
import sys
import collections
import re
import random
import argparse


def timediff(prior, latter):
    mins, secs = str(prior).strip().split('.')
    if len(secs) == 1:
        secs += '0'
    prior_secs = int(mins)*60+int(secs)
    mins, secs = str(latter).strip().split('.')
    if len(secs) == 1:
        secs += '0'
    latter_secs = int(mins)*60+int(secs)
    diff = latter_secs - prior_secs
    diff_mins = diff//60
    diff_secs = diff%60
    return "%d.%d" % (diff_mins, diff_secs)


def event_input(event):

    pass


def tokenize(text):

    text = str(text)
    text = text.replace('\u2013', ' \u2013 ').replace('(', ' ( ').replace(')', ' ) ').replace('.', ' . ').replace(',', ' , ').replace(':', ' : ').replace('-',' - ').replace('—', ' — ')
    text = " ".join( text.split() )

    return text


def print_single(event, home, guest, xml_style=True):
    out = []
    # Define selection and order of information for training input
    #print(event)
    if 'Score' in event:
        event['Score'] = event['Score'].replace('-','\u2013').replace('—', '\u2013') # normalize dash
    if event['Type'] == 'Lopputulos':
        out.append(('type', 'result'))
        out.append(('home', event['Home']))
        out.append(('guest', event['Guest']))
        out.append(('score', event['Score']))
        out.append(('periods', event['Periods']))
        if 'Abbreviations' in event and event['Abbreviations'] != 'noabbr':
            out.append(('abbrevs', event['Abbreviations']))
        #out.append(('time', event['Time']))
    elif event['Type'] == 'Maali':
        out.append(('type', 'goal'))
        out.append(('team', "{team_name} **{x}**".format(team_name=event['Team'], x="home" if event['Team'] == home else "guest")))
        out.append(('player', event['Player']))
        out.append(('assist', event['Assist']))
        if home == event['Team']:
            out.append(('team_score', event['Score'].split('\u2013')[0]))
        elif guest == event['Team']:
            out.append(('team_score', event['Score'].split('\u2013')[1]))
        else:
            out.append(('team_score', '?'))
        out.append(('score', event['Score']))
        out.append(('time', event['Time']))
#        if 'time_diff' in event:
            #out.append(('timediff', timediff(context['last_goal_time'], event['Time'])))
#            out.append(('timediff', event['time_diff']))
        out.append(('period', int(float(event['Time'])//20+1)))
        if 'goal_type' in event:
            out.append(('goaltype', event['goal_type']))
        if 'Abbreviations' in event and event['Abbreviations'] != 'noabbr':
            out.append(('abbrevs', event['Abbreviations']))
        #context['last_goal_time'] = event['Time']
    elif event['Type'] == 'J\u00e4\u00e4hy':
        out.append(('type', 'penalty'))
        out.append(('team', "{team_name} **{x}**".format(team_name=event['Team'], x="home" if event['Team'] == home else "guest")))
        out.append(('player', event['Player']))
        out.append(('minutes', event['Minutes']))
        out.append(('time', event['Time']))
        out.append(('period', int(float(event['Time'])//20+1)))
    elif event['Type'] == 'Torjunnat':
        out.append(('type', 'save'))
        out.append(('team', "{team_name} **{x}**".format(team_name=event['Team'], x="home" if event['Team'] == home else "guest")))
        out.append(('player', event['Player']))
        out.append(('saves', event['Saves']))
        #out.append(('time', event['Time']))
    else:
        # Unrecognized event type, print everything
        for key in event: # Add any information that might have been left out
            if key in ['event_idx']: # Ignore list
                continue
            if key not in dict(out):
                out.append((key, event[key]))

    #out.append(('typestr', event['Type']))

    string = ' '.join([('<%s> %s </%s>' % (k,tokenize(v),k)) if k not in ["type", "period", "minutes", "team_score"] else '<%s>%s</%s>' % (k,tokenize(v),k) for k,v in out])

    text = event['text']
    text = tokenize(text)

    string = "<length>%s</length> " % len( text.split() ) +string

    print(string, text, sep="\t")

    return 


def deciding(score):


    if score == None:
        return None

    s1, s2 = score.split('\u2013')
    s1, s2 = int(s1), int(s2)
    if s1 == s2: # tie
        return None
    loosing_score = min(s1, s2)
    if s1 == loosing_score:
        return re.compile("[0-9]+\u2013{x}".format(x=loosing_score+1))
    if s2 == loosing_score:
        return re.compile("{x}\u2013[0-9]+".format(x=loosing_score+1))

    print("Cannot decide deciding score", score, file=sys.stderr)
    return None
    


def add_game_info(events):

    # 1) timediff
    # 2) first, deciding, last goal
    # 3) final home, guest

    final_score, home_team, guest_team = None, None, None

    # Calculate time diff between goals, and collect final_score/home/guest
    last_goal_time = None
    for i, event in enumerate(events):
        if event['Type'] == 'Maali':
            if last_goal_time:
                events[i]['time_diff'] = timediff(last_goal_time, event['Time'])
            last_goal_time = event['Time']

        if event['Type'] == 'Lopputulos' and final_score == None:
            final_score = event['Score'].replace('-', '\u2013').replace('—', '\u2013') # normalize dash
            home_team = event['Home']
            guest_team = event['Guest']

    # Identify goal types
    deciding_score_regex = deciding(final_score)
    deciding_score = False
    last_goal = "0\u20130"
    for i, event in enumerate(events):
        if event['Type'] == 'Maali':
            types = []
            event["Score"] = event["Score"].replace('-', '\u2013').replace('—', '\u2013')
            if event["Score"] == "0\u20131" or event["Score"] == "1\u20130":
                types.append( "first_goal" )
            if event["Score"] == final_score:
                types.append( "final_goal" )
            if deciding_score_regex is not None and deciding_score == False:
                if deciding_score_regex.match(event["Score"]):
                    types.append( "deciding_goal" )
                    deciding_score = True
            if last_goal != None:
                last_home, last_guest = last_goal.split("\u2013")
                current_home, current_guest = event["Score"].split("\u2013")
                last_home, last_guest, current_home, current_guest = int(last_home), int(last_guest), int(current_home), int(current_guest)
                if current_home == current_guest: # tasoitusmaali
                    types.append( "tasoitus_maali" )
                elif last_home == last_guest and (current_home == last_home+1 or current_guest == last_guest+1): # johtomaali (second part of the if statement must be redundant...)
                    types.append( "leading_goal" )
                elif (current_home == last_home and current_guest < current_home) or (current_guest == last_guest and current_home < current_guest): # kavennusmaali
                    types.append( "kavennus_maali" )
                elif (current_home == last_home and current_guest > current_home+1) or (current_guest == last_guest and current_home > current_guest+1): # kasvattaa johtoa
                    types.append( "increase_lead_goal" )
                else: # happens few times when there is missing events in the input data
                    pass
            if types:
                events[i]["goal_type"] = ", ".join(types)
            last_goal = event["Score"]


    return events, home_team, guest_team





def main(args):

    meta = json.load( open(args.json) )

    event_ref_pat = re.compile("^E\d+$")


    # steps
    # 1) timediff
    # 2) first, deciding, last goal
    # 3) 

    val_size = 250
    for game_i, key in enumerate(meta): # key = game id
        
        events = meta[key]['events']

        events, home, guest = add_game_info(events) # timediff, first/deciding/last goals, home/guest teams

        if events == None:
            continue

        # Events with multiple references
        multi_references = set()
        for event in events:
            if 'text' in event and event_ref_pat.search(event['text']): # Is event reference?
                multi_references.add(event['text'])
                multi_references.add(event['event_idx'])

        # events which should be included in the training data
        reported = []
        for event in events:
            if args.mode != "single":
                print("Mode", args.mode, "not implemented!", file=sys.stderr)
                print("Exiting", file=sys.stderr)
                sys.exit()
            if event['event_idx'] in multi_references:
                continue
            if 'text' not in event or event['text'] == "":
                continue
            reported.append(event)

        # print!
        for event in reported:
            print_single(event, home, guest)





if __name__=="__main__":

    argparser = argparse.ArgumentParser(description='Create training data for the generation model from the annotated json')
    argparser.add_argument('--json', default="", help='annotated json file')
    argparser.add_argument('--output', default="", help='output file names (will be appended with train/dev and input/output)')
    argparser.add_argument('--mode', choices=['single', 'full_report', 'combined_events'], default= "single", help='What type of data to create (single = one input event into one sentence where multiple alignments are skipped -- full_report = sequence of positive events to a full, aligned text -- combined_events = one input into one sentence, but if reference sentence combines multiple events, then input is also combined to include all aligned events)')
    args = argparser.parse_args()

    main(args)
