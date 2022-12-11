import math
from execution_type import Types

class IntermediateRepresentation:
    def __init__(self, name, classes, dimensions, vars, weight_var, encoding, embeddings, debug, encoding_fun,
                 train_size, test_size, num_threads, vector_size, type):
        self.name = name
        self.classes = classes
        self.dimensions = dimensions
        self.vars = vars
        self.weight_var = weight_var
        self.encoding = encoding
        self.embeddings = embeddings
        self.debug = debug
        self.encoding_fun = encoding_fun
        self.type = type
        self.train_size = train_size
        self.test_size = test_size
        self.vector_size = vector_size
        self.num_threads = num_threads

    def define_embeddings(self):
        embedding = ''
        for i in self.embeddings:
            if i[0] == 'LEVEL':
                if i[1] != self.weight_var:
                    embedding += ("\n    " + str(i[1].upper() + " = level_hv(" + 'INPUT_DIM' + ");"))
                else:
                    embedding += ("\n    " + str(i[1].upper() + " = level_hv(" + str(i[1]) + '_DIM' + ");"))
            if i[0] == 'RANDOM':
                if i[1] != self.weight_var:
                    embedding += ("\n    " + str(i[1].upper() + " = random_hv(" + 'INPUT_DIM' + ");"))
                else:
                    embedding += ("\n    " + str(i[1].upper() + " = random_hv(" + str(i[1]) + '_DIM' + ");"))
        return embedding

    # ------------------- DEFINE RUN ------------------- #

    def run(self):
        self.makefile()
        self.define_header()
        self.define_dataset_loaders()
        self.define_math_functions()
        self.define_hdc_functions()
        self.define_train_and_test()
        self.general_main()

    # ------------------- DEFINE MAKEFILE ------------------- #

    def makefile(self):
        if self.type == Types.SEQUENTIAL:
            self.makefile_sequential()
        if self.type == Types.PARALLEL:
            self.makefile_parallel()

    def makefile_sequential(self):
        doto = '.o'
        with open('Makefile', 'w') as file:
            file.write('CC=gcc' + '\n')
            file.write('CFLAGS=-I.' + '\n')
            file.write(self.name + ': ' + self.name + doto + '\n')
            file.write('\t$(CC) -o ' + self.name + ' ' + self.name + doto + ' -lm -O3\n')

    def makefile_parallel(self):
        dotc = '.c'
        with open('Makefile', 'w') as file:
            file.write('CC=gcc' + '\n')
            file.write('all: thread_pool.c thread_pool.h ' + self.name + dotc + '\n')
            file.write('\t$(CC) thread_pool.c ' + self.name + dotc + ' -lpthread -lm -O3 -o ' + self.name + '\n')

    # ------------------- DEFINE HEADER ------------------- #

    def define_header(self):
        if self.type == Types.SEQUENTIAL:
            self.define_header_sequential()
        if self.type == Types.PARALLEL:
            self.define_header_parallel()

    def define_header_sequential(self):
        self.define_include_sequential()
        self.define_constants_sequential()

    def define_header_parallel(self):
        self.define_include_parallel()
        self.define_constants_parallel()

    def define_include_sequential(self):
        with open(self.name.lower() + '.c', 'w') as file:
            file.write('/*********** ' + self.name + ' ***********/\n')
            file.write('#include <stdio.h>\n')
            file.write('#include <stdlib.h>\n')
            file.write('#include <stdint.h>\n')
            file.write('#include <string.h>\n')
            file.write('#include <math.h>\n')
            if self.debug:
                file.write('#include <time.h>\n')
            file.write('#ifndef max\n')
            file.write('#define max(a,b) (((a) > (b)) ? (a) : (b))\n')
            file.write('#endif\n')
            file.write('#ifndef min\n')
            file.write('#define min(a,b) (((a) < (b)) ? (a) : (b))\n')
            file.write('#endif\n')

    def define_constants_sequential(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write('/*********** CONSTANTS ***********/\n')
            file.write('#define TRAIN ' + str(self.train_size) + '\n')
            file.write('#define TEST ' + str(self.test_size) + '\n')

            file.write('#define DIMENSIONS ' + str(self.dimensions) + '\n')
            file.write('#define CLASSES ' + str(self.classes) + '\n')
            file.write('#define VECTOR_SIZE ' + str(self.vector_size) + '\n')
            file.write('float *WEIGHT;\n')
            file.write('typedef float f4si __attribute__ ((vector_size (' + str(self.vector_size) + ')));\n')

            for i in self.embeddings:
                file.write('f4si* ' + str(i[1]) + ';\n')
                if i[1] != self.weight_var:
                    file.write('#define INPUT_DIM ' + str(i[2]) + '\n')
                else:
                    file.write('#define ' + str(i[1]) + '_DIM ' + str(i[2]) + '\n')

            file.write('#define BATCH ' + str(int(self.vector_size / 4)) + '\n')
            file.write('#define NUM_BATCH ' + str(int(self.dimensions / (self.vector_size / 4))) + '\n')

            file.write('float *TRAIN_DATA[TRAIN];\n')
            file.write('float *TRAIN_LABELS[TRAIN];\n')
            file.write('float *TEST_DATA[TEST];\n')
            file.write('float *TEST_LABELS[TEST];\n')

            file.write('struct EncodeTask {\n')
            file.write('    int split_start;\n')
            file.write('    float* indices;\n')
            file.write('    f4si *res;\n')
            file.write('};\n')

    def define_include_parallel(self):
        with open(self.name.lower() + '.c', 'w') as file:
            file.write('/*********** ' + self.name + ' ***********/\n')
            file.write('#include "thread_pool.h"\n')
            file.write('#include <stdio.h>\n')
            file.write('#include <stdlib.h>\n')
            file.write('#include <stdint.h>\n')
            file.write('#include <string.h>\n')
            file.write('#include <math.h>\n')
            file.write('#include <pthread.h>\n')
            if self.debug:
                file.write('#include <time.h>\n')
            file.write('#ifndef max\n')
            file.write('#define max(a,b) (((a) > (b)) ? (a) : (b))\n')
            file.write('#endif\n')
            file.write('#ifndef min\n')
            file.write('#define min(a,b) (((a) < (b)) ? (a) : (b))\n')
            file.write('#endif\n')

    def define_constants_parallel(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write('/*********** CONSTANTS ***********/\n')
            file.write('#define TRAIN ' + str(self.train_size) + '\n')
            file.write('#define TEST ' + str(self.test_size) + '\n')

            file.write('#define DIMENSIONS ' + str(self.dimensions) + '\n')
            file.write('#define CLASSES ' + str(self.classes) + '\n')
            file.write('#define VECTOR_SIZE ' + str(self.vector_size) + '\n')
            file.write('float *WEIGHT;\n')
            file.write('typedef float f4si __attribute__ ((vector_size (' + str(self.vector_size) + ')));\n')

            input_dim = 0
            for i in self.embeddings:
                file.write('f4si* ' + str(i[1]) + ';\n')
                if i[1] != self.weight_var:
                    file.write('#define INPUT_DIM ' + str(i[2]) + '\n')
                    input_dim = i[2]
                else:
                    file.write('#define ' + str(i[1]) + '_DIM ' + str(i[2]) + '\n')

            file.write('#define BATCH ' + str(int(self.vector_size / 4)) + '\n')
            file.write('#define NUM_BATCH ' + str(int(self.dimensions / (self.vector_size / 4))) + '\n')
            file.write('#define NUM_THREADS ' + str(self.num_threads) + '\n')
            file.write('#define SPLIT_SIZE ' + str(math.floor(input_dim / self.num_threads)) + '\n')
            file.write('#define SIZE ' + str(math.floor(input_dim / self.num_threads) * self.num_threads) + '\n')

            file.write('float *TRAIN_DATA[TRAIN];\n')
            file.write('float *TRAIN_LABELS[TRAIN];\n')
            file.write('float *TEST_DATA[TEST];\n')
            file.write('float *TEST_LABELS[TEST];\n')
            file.write('ThreadPool *pool;\n')

            file.write('struct EncodeTask {\n')
            file.write('    int split_start;\n')
            file.write('    float* indices;\n')
            file.write('    f4si *res;\n')
            file.write('};\n')

    # ------------------- DEFINE DATA LOADERS ------------------- #

    def define_dataset_loaders(self):
        if self.type == Types.SEQUENTIAL:
            self.define_dataset_loader_sequential()
        if self.type == Types.PARALLEL:
            self.define_dataset_loader_parallel()

    def define_dataset_loader_sequential(self):
        self.load_data()
        self.load_labels()
        self.load_dataset()

    def define_dataset_loader_parallel(self):
        self.load_data()
        self.load_labels()
        self.load_dataset()

    def load_data(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
void load_data(float* data[], char* path){
    FILE * fp;
    char * line = NULL;
    size_t len = 0;
    ssize_t read;
    fp = fopen(path, "r");
    if (fp == NULL)
        exit(EXIT_FAILURE);
    char* token;
    int count = 0;
    while ((read = getline(&line, &len, fp)) != -1) {
        token = strtok(line, ",");
        for (int i = 0; i < INPUT_DIM; i++){
          *(data[count] + i) = (float) atof(token);
          token = strtok(NULL, ",");
        }
        count += 1;
    }
    fclose(fp);
    if (line)
        free(line);
}
            '''
            )

    def load_labels(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
void load_label(float* data[], char* path){
    FILE * fp;
    char * line = NULL;
    size_t len = 0;
    ssize_t read;
    fp = fopen(path, "r");
    if (fp == NULL)
        exit(EXIT_FAILURE);
    char* token;
    int count = 0;
    while ((read = getline(&line, &len, fp)) != -1) {
        *(data[count]) = atoi(line);
        count += 1;
    }
    fclose(fp);
    if (line)
        free(line);
}       
                '''
            )

    def load_dataset(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
void load_dataset(char **argv){
    for (int i = 0; i < TRAIN; i++){
        TRAIN_DATA[i] = (float *) calloc(INPUT_DIM, sizeof(float));
        TRAIN_LABELS[i] = (float *) calloc(1, sizeof(int));
    }

    for (int i = 0; i < TEST; i++){
        TEST_DATA[i] = (float *) calloc(INPUT_DIM, sizeof(float));
        TEST_LABELS[i] = (float *) calloc(1, sizeof(int));
    }

    load_data(TRAIN_DATA, argv[1]);
    load_data(TEST_DATA, argv[3]);
    load_label(TRAIN_LABELS, argv[2]);
    load_label(TEST_LABELS, argv[4]);
}
                '''
            )

    # ------------------- DEFINE MATH FUNCTIONS ------------------- #

    def define_math_functions(self):
        if self.type == Types.SEQUENTIAL:
            self.define_math_functions_sequential()
        if self.type == Types.PARALLEL:
            self.define_math_functions_parallel()

    def define_math_functions_sequential(self):
        self.define_random_number()
        self.define_random_vector()
        self.define_weights()
        self.define_update_weights()
        self.define_linear()
        self.define_norm2()
        self.define_normalize()
        self.define_argmax()
        self.define_map_range_clamp()
        self.define_hard_quantize()

    def define_math_functions_parallel(self):
        self.define_random_number()
        self.define_random_vector()
        self.define_weights()
        self.define_update_weights()
        self.define_linear()
        self.define_norm2()
        self.define_normalize()
        self.define_argmax()
        self.define_map_range_clamp()
        self.define_hard_quantize()

    def define_random_number(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
float get_rand(float low_bound, float high_bound){
    return (float) ((float)rand() / (float)RAND_MAX) * (high_bound - low_bound) + low_bound;
}
                '''
            )

    def define_random_vector(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
f4si *random_vector(int size, float low_bound, float high_bound){
   f4si *arr = calloc(size * DIMENSIONS, sizeof(float));
   int i, j, k;
   for (i = 0; i < size; i++){
      for (j = 0; j < NUM_BATCH; j++){
         for(k = 0; k < BATCH; k++){
            arr[i*NUM_BATCH+j][k] = get_rand(low_bound, high_bound);
         }
      }
   }
   return arr;
}
                '''
            )

    def define_weights(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
void weights(){
    WEIGHT = (float *)calloc(CLASSES * DIMENSIONS, sizeof(float));
}
                    '''
            )

    def define_update_weights(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
void update_weight(float* encoding, int feature){
    int i;
    for(i = 0; i < DIMENSIONS; i++){
        *(WEIGHT + feature*DIMENSIONS + i) += (float)*(encoding + i);
    }
}
                    '''
            )

    def define_linear(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
float* linear(float* m){
    int j, k;
    float *arr = (float *)calloc(CLASSES, sizeof(float));
    for (j = 0; j < DIMENSIONS; ++j) {
      for (k = 0; k < CLASSES; ++k) {
         *(arr + k) += (float)*(m + j) * *(WEIGHT + k*DIMENSIONS + j);
      }
   }
    return arr;
}
                    '''
            )

    def define_norm2(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
float norm2(int feature){
   float norm = 0.0;
   int i;
   for (i = 0; i < DIMENSIONS; i++){
      norm += *(WEIGHT + feature*DIMENSIONS + i) * *(WEIGHT + feature*DIMENSIONS + i);
   }
   return sqrt(norm);
}
                    '''
            )

    def define_normalize(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
void normalize(){
   float eps = 1e-12;
   int i, j;
   for (i = 0; i < CLASSES; i++){
      float norm = norm2(i);
      for (j = 0; j < DIMENSIONS; j++){
        *(WEIGHT + i*DIMENSIONS + j) = *(WEIGHT + i*DIMENSIONS + j) / max(norm,eps);
      }
   }
}
                    '''
            )

    def define_argmax(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
int argmax(float* classify){
   int i;
   int max_i = 0;
   float max = 0;
   for (i = 0; i < CLASSES; i++){
       if(*(classify + i) > max){
           max = *(classify + i);
           max_i = i;
       }
   }
   return max_i;
}
                    '''
            )

    def define_map_range_clamp(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
float** map_range_clamp(float* arr[], int size, float out_max, float* res[]){
   float in_min = 0;
   float in_max = 1;
   float out_min = 0;
   int i, j;
   for (i = 0; i < size; i++){
      for (j = 0; j < INPUT_DIM; j++){
        float map_range = round(out_min + (out_max - out_min) * (*(arr[i] + j) - in_min) / (in_max - in_min));
        *(res[i] + j) = min(max(map_range,out_min),out_max);
      }
      free(arr[i]);
   }
   return res;
}
                    '''
            )

    def define_hard_quantize(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
void hard_quantize(float *arr, int size){
   int i, j;
   for (i = 0; i < size; i++){
      for (j = 0; j < DIMENSIONS; j++){
        int value = *(arr + i*DIMENSIONS + j);
        if (value > 0){
          *(arr + i*DIMENSIONS + j) = 1.0;
        } else {
            *(arr + i*DIMENSIONS + j) = -1.0;
        }
      }
   }
}
                    '''
            )

    # ------------------- DEFINE HDC FUNCTIONS ------------------- #


    def define_hdc_functions(self):
        if self.type == Types.SEQUENTIAL:
            self.define_hdc_functions_sequential()
        if self.type == Types.PARALLEL:
            self.define_hdc_functions_parallel()

    def define_hdc_functions_sequential(self):
        self.define_random_hv()
        self.define_level_hv()
        self.define_encoding_function_sequential()
        self.define_encoding_sequential()

    def define_hdc_functions_parallel(self):
        self.define_random_hv()
        self.define_level_hv()
        self.define_encoding_function_parallel()
        self.define_encoding_parallel()

    def define_random_hv(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
f4si *random_hv(int size){
   f4si *arr = calloc(size * DIMENSIONS, sizeof(float));
   int P = 50;
   int i, j, k;
   for (i = 0; i < size; i++){
      for (j = 0; j < NUM_BATCH; j++){
         for(k = 0; k < BATCH; k++){
            arr[i*NUM_BATCH+j][k] = rand() % 100 > P ? 1 : -1;
         }
      }
   }
   return arr;
}
                    '''
            )

    def define_level_hv(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
f4si *level_hv(int levels){
    int levels_per_span = levels-1;
    int span = 1;
    f4si *span_hv = random_hv(span+1);
    f4si *threshold_hv = random_vector(span,0,1);
    f4si *hv = calloc(levels * DIMENSIONS, sizeof(float));
    int i, j, k;
    for(i = 0; i < levels; i++){
        float t = 1 - ((float)i / levels_per_span);
        for(j = 0; j < NUM_BATCH; j++){
            for(k = 0; k < BATCH; k++){
                if((t > threshold_hv[j][k] || i == 0) && i != levels-1){
                    hv[i*NUM_BATCH+j][k] = span_hv[0*NUM_BATCH+j][k];
                } else {
                    hv[i*NUM_BATCH+j][k] = span_hv[1*NUM_BATCH+j][k];
                }
             }
        }
    }
    return hv;
}
                    '''
            )

    def define_encoding_function_sequential(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(self.encoding_fun)

    def define_encoding_sequential(self):
        """Generates the encoding"""
        with open(self.name.lower() + '.c', 'a') as file:
            file.write('''
float* encodings(float* x){
    float* enc = (float*)encode_function(x);
    hard_quantize(enc,1);
    return enc;
}
                ''')

    def define_encoding_function_parallel(self):
        with open(self.name.lower() + '.c', 'a') as file:
            print('enc', self.encoding_fun)
            file.write(self.encoding_fun)

    def define_encoding_parallel(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
f4si *encode_function(float* indices){
    struct EncodeTask *task = (struct EncodeTask *)malloc(sizeof(struct EncodeTask));
    f4si *res = calloc(DIMENSIONS,sizeof(int));
    for (int i = 0; i < NUM_THREADS; i++) {
        struct EncodeTask *task = (struct EncodeTask *)malloc(sizeof(struct EncodeTask));
        task -> split_start = i*SPLIT_SIZE;
        task -> indices = indices;
        task -> res = res;
        mt_add_job(pool, &encode_fun, task);
    }
    return res;
}

float* encodings(float* x){
    float* enc = (float*)encode_function(x);
    hard_quantize(enc,1);
    return enc;
}
                ''')

    # ------------------- DEFINE TRAIN AND TEST ------------------- #

    def define_train_and_test(self):
        if self.type == Types.SEQUENTIAL:
            self.define_train_and_test_sequential()
        if self.type == Types.PARALLEL:
            self.define_train_and_test_parallel()

    def define_train_and_test_sequential(self):
        self.define_train_loop_sequential()
        self.define_test_loop_sequential()

    def define_train_and_test_parallel(self):
        self.define_train_loop_parallel()
        self.define_test_loop_parallel()

    def define_train_loop_sequential(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
void train_loop(){
    float *res[TRAIN];
    int i;
    for (i = 0; i < TRAIN; i++){
        res[i] = (float *)calloc(INPUT_DIM, sizeof(float));
    }
    map_range_clamp(TRAIN_DATA,TRAIN,''' + self.weight_var + '''_DIM-1, res);
    for(i = 0; i < TRAIN; i++){
        float* enc = encodings(res[i]);
        update_weight(enc,*(TRAIN_LABELS[i]));
        free(res[i]);
        free(enc);
    }
    normalize();
}
                    '''
            )

    def define_test_loop_sequential(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                    '''
float test_loop(){
    float *res[TEST];
    int i;
    for (i = 0; i < TEST; i++){
        res[i] = (float *)calloc(INPUT_DIM, sizeof(float));
    }
    map_range_clamp(TEST_DATA,TEST,''' + self.weight_var + '''_DIM-1, res);
    int correct_pred = 0;
    for(i = 0; i < TEST; i++){
        float* enc = encodings(res[i]);
        float *l = linear(enc);
        int index = argmax(l);
        if((int)index == (int)*(TEST_LABELS[i])){
            correct_pred += 1;
        }
        free(l);
        free(res[i]);
        free(enc);
    }
    return correct_pred/(float)TEST;
}
                    '''
                )

    def define_train_loop_parallel(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
void train_loop(){
    float *res[TRAIN];
    float *enc[TRAIN];
    int i;
    for (i = 0; i < TRAIN; i++){
        res[i] = (float *)calloc(INPUT_DIM, sizeof(float));
        enc[i] = (float *)calloc(DIMENSIONS, sizeof(float));
    }
    map_range_clamp(TRAIN_DATA,TRAIN,''' + self.weight_var + '''_DIM-1, res);
    for(i = 0; i < TRAIN; i++){
        enc[i] = encodings(res[i]);
    }
    mt_join(pool);
    for(i = 0; i < TRAIN; i++){
        update_weight(enc[i],*(TRAIN_LABELS[i]));
        free(res[i]);
        free(enc[i]);
    }
    normalize();
}
                    '''
            )

    def define_test_loop_parallel(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
float test_loop(){
    float *res[TEST];
    float *enc[TEST];
    int i;
    for (i = 0; i < TEST; i++){
        res[i] = (float *)calloc(INPUT_DIM, sizeof(float));
        enc[i] = (float *)calloc(DIMENSIONS, sizeof(float));
    }
    map_range_clamp(TEST_DATA,TEST,''' + self.weight_var + '''_DIM-1, res);
    int correct_pred = 0;
    for(i = 0; i < TEST; i++){
        enc[i] = encodings(res[i]);
    }
    mt_join(pool);
    for(i = 0; i < TEST; i++){
        float *l = linear(enc[i]);
        int index = argmax(l);
        if((int)index == (int)*(TEST_LABELS[i])){
            correct_pred += 1;
        }
        free(l);
        free(res[i]);
        free(enc[i]);
    }
    return correct_pred/(float)TEST;
}
                    '''
            )

    # ------------------- DEFINE TRAIN AND TEST ------------------- #

    def general_main(self):
        if self.type == Types.SEQUENTIAL:
            self.general_main_sequential()
        if self.type == Types.PARALLEL:
            self.general_main_parallel()

    def general_main_sequential(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
int main(int argc, char **argv) {
    '''
                +
                str(self.define_embeddings())
                +
                '''
    weights();
    load_dataset(argv);
    '''
            )
            if self.debug:
                file.write(
                    '''
    struct timespec begin, end;
    double elapsed;
    clock_gettime(CLOCK_MONOTONIC, &begin);
                    '''
                )

            file.write(
                '''
    train_loop();
    float acc = test_loop();
                        ''')
            if self.debug:
                file.write(
                    '''
    clock_gettime(CLOCK_MONOTONIC, &end);
    elapsed = end.tv_sec - begin.tv_sec;
    elapsed += (end.tv_nsec - begin.tv_nsec) / 1000000000.0;
    printf("%d, %f, %f \\n", DIMENSIONS,elapsed, acc);
                    '''
                )
            else:
                file.write(
                    '''
        printf("%d, %f \\n", DIMENSIONS, acc);
                    '''
                )

            file.write(
                '''
    }              
                '''
            )

    def general_main_parallel(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
int main(int argc, char **argv) {
    '''
                +
                str(self.define_embeddings())
                +
                '''
	pool = mt_create_pool(NUM_THREADS);
    weights();
    load_dataset(argv);
    '''
            )
            if self.debug:
                file.write(
                    '''
    struct timespec begin, end;
    double elapsed;
    clock_gettime(CLOCK_MONOTONIC, &begin);
                    '''
                )

            file.write(
                '''
    train_loop();
    float acc = test_loop();
                        ''')
            if self.debug:
                file.write(
                    '''
    clock_gettime(CLOCK_MONOTONIC, &end);
    elapsed = end.tv_sec - begin.tv_sec;
    elapsed += (end.tv_nsec - begin.tv_nsec) / 1000000000.0;
    printf("%d, %f, %f \\n", DIMENSIONS,elapsed, acc);
                    '''
                )
            else:
                file.write(
                    '''
        printf("%d, %f \\n", DIMENSIONS, acc);
                    '''
                )

            file.write(
                '''
}              
                '''
            )
