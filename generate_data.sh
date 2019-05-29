
current=`pwd`

# join annotations
cd /home/jmnybl/git_checkout/hockey-annotation
python3 ../data-processing/join_annotations.py train.json events.txt annotated-train.json
python3 ../data-processing/join_annotations.py devel.json events.txt annotated-devel.json

cd $current

for m in "single" "combined_events" "full_report"
do

    
    data="training_data_$m"
    model="hockey_model_$m"

    mkdir -p $data
    mkdir -p $model
 
    rm $model/*

    mkdir -p $data/ready

    python3 create_training_data.py --json ../hockey-annotation/annotated-train.json --mode $m --extra_testfile $data/empty_train_games.input | shuf > $data/train.all
    python3 create_training_data.py --json ../hockey-annotation/annotated-devel.json --mode $m | shuf > $data/devel.all

    cat $data/train.all | cut -f 1 > $data/ready/train.input
    cat $data/train.all | cut -f 2 > $data/ready/train.output

    cat $data/devel.all | cut -f 1 > $data/ready/devel.input
    cat $data/devel.all | cut -f 2 > $data/ready/devel.output

done
