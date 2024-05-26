SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR

comp(){
    python3 ../src/main.py $1.hdcc
}

PROFILE_CMD() {
    gp-collect-app -O test.er -p on -S on $@
}

profile(){
    comp $1
    sed -i -e "s/-O3/-O3 -pg -g/" Makefile
    make > /dev/null 2>&1
    rm Makefile
    PROFILE_CMD ./$1 ../data/$2/$3_train_data ../data/$2/$3_train_labels ../data/$2/$3_test_data ../data/$2/$3_test_labels
    echo "" 
    gp-display-gui test.er
}

run(){
    make > /dev/null 2>&1
    ./$1 ../data/$2/$3_train_data ../data/$2/$3_train_labels ../data/$2/$3_test_data ../data/$2/$3_test_labels
    echo ""
}

comp_n_run(){
    comp $1
    run $1 $2 $3
    rm Makefile
}

#profile mnist MNIST mnist

comp_n_run emgp EMG patient_1
comp_n_run emgpp EMG patient_2
comp_n_run emgppp EMG patient_3
comp_n_run emgpppp EMG patient_4
comp_n_run emgppppp EMG patient_5

#time run emgp EMG patient_1