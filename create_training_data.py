import json
import sys
import collections
import re
import random


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


def generate_input(event, context, xml_style=True):
    out = []
    # Define selection and order of information for training input
    #print(event)
    if 'Score' in event:
        event['Score'] = event['Score'].replace('-','\u2013')
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
        out.append(('team', event['Team']))
        out.append(('player', event['Player']))
        out.append(('assist', event['Assist']))
        if 'home_team' in context and context['home_team'] == event['Team']:
            out.append(('team_score', event['Score'].split('\u2013')[0]))
        elif 'guest_team' in context and context['guest_team'] == event['Team']:
            try:
                out.append(('team_score', event['Score'].split('\u2013')[1]))
            except IndexError:
                out.append(('team_score', event['Score'].split('-')[1]))
        else:
            out.append(('team_score', '?'))
        out.append(('score', event['Score']))
        out.append(('time', event['Time']))
        if 'time_diff' in event:
            #out.append(('timediff', timediff(context['last_goal_time'], event['Time'])))
            out.append(('timediff', event['time_diff']))
        out.append(('period', int(float(event['Time'])//20+1)))
        goal_types = []
        if 'final_score' in context and event['Score'] == context['final_score']:
            goal_types.append('final')
        if 'deciding_goal' in context and context['deciding_goal'] == event['Score']:
            goal_types.append('deciding')
        if goal_types:
            out.append(('goaltype', ', '.join(goal_types)))
        if 'Abbreviations' in event and event['Abbreviations'] != 'noabbr':
            out.append(('abbrevs', event['Abbreviations']))
        #context['last_goal_time'] = event['Time']
    elif event['Type'] == 'J\u00e4\u00e4hy':
        out.append(('type', 'penalty'))
        out.append(('team', event['Team']))
        out.append(('player', event['Player']))
        out.append(('minutes', event['Minutes']))
        out.append(('time', event['Time']))
    elif event['Type'] == 'Torjunnat':
        out.append(('type', 'save'))
        out.append(('team', event['Team']))
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
    if xml_style:
        string = ' '.join([('<%s> %s </%s>' % (k,v,k)) for k,v in out])
    else:
        #string = ' ; '.join(['%s = \' %s \'' % (k,v) for k,v in out])
        string = ' ; '.join(['%s = %s' % (k,v) for k,v in out])
        #return ' '.join([('%s' % (v)).replace('\u2013', ' \u2013 ') for k,v in out])

    string = string.replace('\u2013', ' \u2013 ').replace('(', ' ( ').replace(')', ' ) ').replace('.', ' . ').replace(',', ' , ')
    return re.sub(" +", " ", string)


if len(sys.argv) < 2:
    print("Usage: %s <annotated events JSON meta file>" % sys.argv[0], file=sys.stderr)
    sys.exit()

meta = json.load(open(sys.argv[1]))

event_ref_pat = re.compile("^E\d+$")

input_file = open("train_input.txt", 'w')
output_file = open("train_output.txt", 'w')

input_val_file = open("val_input.txt", 'w')
output_val_file = open("val_output.txt", 'w')

selection_file = open("selection_train.jsonl", 'w')
selection_val_file = open("selection_val.jsonl", 'w')

val_size = 250
for game_i, key in enumerate(meta):
    # Calculate time diff between goals
    last_goal_time = None
    for event in meta[key]['events']:
        if event['Type'] == 'Maali':
            if last_goal_time:
                event['time_diff'] = timediff(last_goal_time, event['Time'])
            last_goal_time = event['Time']

    # Collect events with mentions
    entries = collections.defaultdict(lambda: [])
    context = {}
    for event in meta[key]['events']:
        if event['Type'] == 'Lopputulos':
            context['final_score'] = event['Score']
            context['home_team'] = event['Home']
            context['guest_team'] = event['Guest']

        event['game'] = key
        if 'text' in event:
            #print(event)
            event['reported'] = 1
            if event_ref_pat.search(event['text']): # Is event reference?
                entries[event['text']].append(event)
            else:
                entries[event['event_idx']].append(event)
        else:
            event['reported'] = 0
            entries[event['event_idx']].append(event)

    if not entries:
        continue

    print()
    print("GAME:", key)

    # Identify deciding goal
    last_score = None
    loosing_score = None
    for event in meta[key]['events'][::-1]:
        if event['Type'] == 'Maali':
            try:
                s1, s2 = event['Score'].split('\u2013')
            except ValueError:
                try:
                    s1, s2 = event['Score'].split('-')
                except ValueError:
                    print("Parse error in %s: %s" % (key, event['Score']), file=sys.stderr)
                    raise
            s1, s2 = int(s1), int(s2)
            if last_score is None:
                loosing_score = min(s1, s2)
            if loosing_score and max(s1, s2) == loosing_score+1:
                context['deciding_goal'] = event['Score']
            if s1 == s2:
                break
            last_score = event['Score']

    # Print results
    empty_game = True
    for events in entries.values():
        for event in events:
            if event['reported'] == 1:
                empty_game = False
    for idx, events in entries.items():
        text = None
        inputs = []
        for event in events:
            input = generate_input(event, context, xml_style=False)
            event['input'] = input
            if not empty_game:
                if val_size < 0:
                    selection_file.write(json.dumps(event)+'\n')
                else:
                    selection_val_file.write(json.dumps(event)+'\n')
            if event['reported'] == 0:
                continue
            print('   IN:', input)
            inputs.append(input)
            if not event_ref_pat.search(event['text']):
                text = event['text']
            if not text:
                continue

        char_level = False
        if char_level:
            delim = ' '
        else:
            delim = ''

        if text:
            print('   OUT:', text)
            print()
            if len(inputs)==1:# len(inputs)==1 #and event['Type'] in ['Maali']:
                input = inputs[0]+'\n'
                #input = 'events = %d | ' % len(inputs) + '|'.join(inputs)+'\n'
                #output = event['Type']+': '+text.replace('\u2013', ' \u2013 ').replace('(', ' ( ').replace(')', ' ) ').replace('.', ' . ').replace(',', ' , ')+'\n'
                output = text.replace('\u2013', ' \u2013 ').replace('(', ' ( ').replace(')', ' ) ').replace('.', ' . ').replace(',', ' , ')
                output = "<%s> %s </%s>\n" % (event['Type'], output, event['Type'])

                if val_size > 0:# and random.random() < 0.1:
                    input_val_file.write(delim.join(input))
                    output_val_file.write(delim.join(output))
                else:
                    input_file.write(delim.join(input))
                    output_file.write(delim.join(output))
            else:
                pass

    val_size -= 1


input_file.close()
output_file.close()
input_val_file.close()
output_val_file.close()
selection_file.close()
selection_val_file.close()
