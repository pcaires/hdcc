import math


def generate(length, shift):
    s = ''
    length = int(length)
    for i in range(length):
        if i < shift:
            s += ',' + str(length - shift + i)
        else:
            s += ',' + str((i - shift))
    return s


def generate_shuffle(n, vector_size):
    sif = ''
    for i in range(1, n):
        sif += '''
    if (d == ''' + str(i) +'''){
        res = __builtin_shufflevector(arr,arr''' + generate(vector_size / 4, i) + ''');
        return res;
    }'''
    shuffle = '''
f4si shuffle(f4si arr, int d){
    f4si res;
    ''' + sif + '''
    return res;
}
    '''
    return shuffle


class ParallelRepresentation:
    def __init__(self, name, classes, dimensions, vars, weight_var, encoding, embeddings, debug, encoding_fun,
                 train_size, test_size, num_threads, vector_size, type, input_dim, high, basic, padding, permutes,
                 ngram, path, not_multiset, vectorial, performance):
        self.n = name
        self.path = path
        self.name = self.path + self.n
        self.basic_name = self.get_basic_name(name)
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
        self.input_dim = input_dim
        self.high = high
        self.basic = basic
        self.padding = padding
        self.permutes = permutes
        self.ngram_perm = ngram
        self.not_multiset = not_multiset
        self.vectorial = vectorial
        self.performance = performance

    def get_basic_name(self, name):
        temp = len(name)
        for c in name:
            if c.isdigit():
                temp = name.index(c)
                break
        return name[0:temp]

    def define_embeddings(self):
        embedding = ''
        for i in self.embeddings:
            if i[0] == 'LEVEL':
                if i[1] == self.weight_var:
                    embedding += ("\n    " + str(i[1].upper() + " = level_hv(" + str(i[1]) + '_DIM' + ");"))
                else:
                    embedding += ("\n    " + str(i[1].upper() + " = level_hv(" + str(i[1]) + '_DIM' + ");"))
            if i[0] == 'RANDOM':
                if i[1] == self.weight_var:
                    embedding += ("\n    " + str(i[1].upper() + " = random_hv(" + str(i[1]) + '_DIM' + ");"))
                else:
                    embedding += ("\n    " + str(i[1].upper() + " = random_hv(" + str(i[1]) + '_DIM' + ");"))
            if i[0] == 'RANDOM_PADDING':
                if i[1] == self.weight_var:
                    embedding += ("\n    " + str(i[1].upper() + " = random_hv(" + str(i[1]) + '_DIM' + ");"))
                else:
                    embedding += ("\n    " + str(i[1].upper() + " = random_hv(" + str(i[1]) + '_DIM' + ");"))
        return embedding

    def run_parallel(self):
        self.makefile()
        self.define_header()
        self.define_dataset_loaders()
        self.define_math_functions()
        self.define_hdc_functions()
        self.define_train_and_test()
        self.general_main()

    def makefile(self):
        dotc = '.c'
        import os
        cwd = os.getcwd()
        with open(str(cwd)+'/Makefile', 'w') as file:
            file.write('CC=clang' + '\n')
            file.write('all: ../src/thread_pool.c ../src/thread_pool.h ' + self.name + dotc + '\n')
            file.write('\t$(CC) ../src/thread_pool.c ' + self.name + dotc + ' -lpthread -lm -O3 -o ' + self.name + '\n')

    def define_header(self):
        self.define_include()
        self.define_constants()

    def define_include(self):
        with open(self.name.lower() + '.c', 'w') as file:
            file.write('/*********** ' + self.name + ' ***********/\n')
            file.write('#include "../src/thread_pool.h"\n')
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

    def define_constants(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write('/*********** CONSTANTS ***********/\n')
            file.write('#define TRAIN ' + str(self.train_size) + '\n')
            file.write('#define TEST ' + str(self.test_size) + '\n')

            file.write('#define DIMENSIONS ' + str(self.dimensions) + '\n')
            file.write('#define CLASSES ' + str(self.classes) + '\n')
            file.write('#define VECTOR_SIZE ' + str(self.vector_size) + '\n')
            file.write('float *WEIGHT;\n')
            if self.vectorial:
                file.write('typedef float f4si __attribute__ ((vector_size (' + str(self.vector_size) + ')));\n')

            file.write('#define INPUT_DIM ' + str(self.input_dim) + '\n')

            for i in self.embeddings:
                if self.vectorial:
                    file.write('f4si* ' + str(i[1]) + ';\n')
                else:
                    file.write('float* ' + str(i[1])+ ';\n')
                file.write('#define ' + str(i[1]) + '_DIM ' + str(i[2]) + '\n')

            file.write('#define BATCH ' + str(int(self.vector_size / 4)) + '\n')
            file.write('#define NUM_BATCH ' + str(int(self.dimensions / (self.vector_size / 4))) + '\n')
            file.write('#define NUM_THREADS ' + str(self.num_threads) + '\n')
            file.write('#define SPLIT_SIZE ' + str(math.floor(self.input_dim / self.num_threads)) + '\n')
            file.write('#define SIZE ' + str(math.floor(self.input_dim / self.num_threads) * self.num_threads) + '\n')
            file.write('#define HIGH ' + str(self.high) + '\n')
            file.write('int CORRECT_PREDICTIONS;\n')

            file.write('ThreadPool *pool;\n')

            file.write('struct DataReader {\n')
            file.write('    char *path;\n')
            file.write('    FILE *fp;\n')
            file.write('    char * line;\n')
            file.write('    size_t len;\n')
            file.write('    ssize_t read;\n')
            file.write('};\n')

            file.write('struct DataReader* train_data;\n')
            file.write('struct DataReader* train_labels;\n')
            file.write('struct DataReader* test_data;\n')
            file.write('struct DataReader* test_labels;\n')

            file.write('struct Task {\n')
            file.write('    float* data;\n')
            file.write('    int label;\n')
            file.write('};\n')

            if self.padding is not None:
                file.write('float padding = '+str(self.padding)+'.0;')
            else:
                file.write('float padding = -1.0;')

    def define_dataset_loaders(self):
        self.set_data_loaders()
        self.load_data()
        self.load_labels()
        self.load_dataset()
        self.close_files()

    def set_data_loaders(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
struct DataReader* set_load_data(char* path, struct DataReader* data_reader){
    data_reader = (struct DataReader *)calloc(1, sizeof(struct DataReader));
    data_reader -> path = path;
    data_reader -> fp = fopen(path, "r");
    data_reader -> line = NULL;
    data_reader -> len = 0;

    if (data_reader -> fp == NULL)
        exit(EXIT_FAILURE);

    return data_reader;
}
            '''
            )

    def load_data(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
float* load_data_next_line(struct DataReader* data_reader){
float* data = (float *) calloc(INPUT_DIM, sizeof(float));
char* token;
if ((data_reader -> read = getline(&data_reader -> line, &data_reader -> len, data_reader -> fp)) != -1) {
    token = strtok(data_reader -> line, ",");
    for (int i = 0; i < INPUT_DIM; i++){
      *(data + i) = (float) atof(token);
      token = strtok(NULL, ",");
    }
}
return data;
}
            '''
            )

    def load_labels(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
int load_labels_next_line(struct DataReader* data_reader){
    int label;
    char* token;
    if ((data_reader -> read = getline(&data_reader -> line, &data_reader -> len, data_reader -> fp)) != -1) {
         label = atoi(data_reader -> line);
    }
    return label;
}
                '''
            )

    def load_dataset(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
void prepare_to_load_data(char **argv){
    train_data = set_load_data(argv[1], train_data);
    train_labels = set_load_data(argv[2], train_labels);
    test_data = set_load_data(argv[3], test_data);
    test_labels = set_load_data(argv[4], test_labels);
}
                '''
            )

    def close_files(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
void close_file(struct DataReader* data_reader){
    fclose(data_reader -> fp );
    if (data_reader -> line)
        free(data_reader -> line);
}
                '''
            )


    def define_math_functions(self):
        self.define_random_number()
        self.define_random_vector()
        self.define_weights()
        self.define_update_weights()
        self.define_update_correct_predictions()
        self.define_linear()
        self.define_norm2()
        self.define_normalize()
        self.define_argmax()
        self.define_map_range_clamp_one()
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
            if self.vectorial:
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
            else:
                file.write(
                    '''
float *random_vector(int size, float low_bound, float high_bound){
   float *arr = calloc(size * DIMENSIONS, sizeof(float));
   int i, j, k;
   for (i = 0; i < size; i++){
      for (j = 0; j < DIMENSIONS; j++){
        arr[(i*DIMENSIONS)+j] = get_rand(low_bound, high_bound);
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

    def define_update_correct_predictions(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
void update_correct_predictions(){
    lock_condition(pool);
    CORRECT_PREDICTIONS += 1;
    unlock_condition(pool);
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

    def define_map_range_clamp_one(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
void map_range_clamp_one(float* arr, float out_max, float* res){
    float in_min = 0;
    float in_max = HIGH;
    float out_min = 0;
    int i, j;
    for (j = 0; j < INPUT_DIM; j++){
        float map_range = round(out_min + (out_max - out_min) * (*(arr + j) - in_min) / (in_max - in_min));
        *(res + j) = min(max(map_range,out_min),out_max);
    }
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

    def multibind(self):
        """Binds a set of hypervectors together"""
        with open(self.name.lower() + '.c', 'a') as file:
            if self.vectorial:
                file.write(
                '''
f4si *multibind(f4si *a, f4si *b){
    int i, j;
    for(i = 0; i < INPUT_DIM; ++i){
        for(j = 0; j < NUM_BATCH; j++){
             b[(NUM_BATCH * i) + j] = a[(NUM_BATCH * i) + j] * b[(NUM_BATCH * i) + j];
        }
    }
    return b;
}
                '''
            )
            else:
                file.write(
                '''
float *multibind(float *a, float *b){
    int i, j;
    for(i = 0; i < INPUT_DIM; ++i){
        for(j = 0; j < DIMENSIONS; j++){
             b[(DIMENSIONS * i) + j] = a[(DIMENSIONS * i) + j] * b[(DIMENSIONS * i) + j];
        }
    }
    return b;
}
                '''
            )

    def multibind_forward(self):
        """Binds a set of hypervectors together"""
        with open(self.name.lower() + '.c', 'a') as file:
            if self.vectorial:
                file.write(
                '''
f4si *multibind_forward(f4si *a, f4si *b, float* indices, f4si* enc){
    int i, j;
    for(i = 0; i < INPUT_DIM; ++i){
        for(j = 0; j < NUM_BATCH; j++){
            if (indices[i] != padding){
                enc[(NUM_BATCH * i) + j] = a[(NUM_BATCH * i) + j] * b[((int)indices[i]*NUM_BATCH) + j];
            } else {
                enc[(NUM_BATCH * i) + j] *= 0;
            }
        }
    }
    return enc;
}
                '''
            )
            else:
                file.write(
                '''
float *multibind_forward(float *a, float *b, float* indices, float* enc){
    int i, j;
    for(i = 0; i < INPUT_DIM; ++i){
        for(j = 0; j < DIMENSIONS; j++){
            if (indices[i] != padding){
                enc[(DIMENSIONS * i) + j] = a[(DIMENSIONS * i) + j] * b[(int)indices[i]* DIMENSIONS + j];
            } else {
                enc[(DIMENSIONS * i) + j] *= 0;
            }
        }
    }
    return enc;
}

                '''
            )

    def ngram(self):
        '''
f4si* ngram_forward(f4si* arr, float* indices, f4si* enc, const int d){
    int i, j, k;
    f4si aux;
    f4si *forward_arr = calloc(DIMENSIONS * d, sizeof(int));
    f4si actual;
    float m[d];
    float p[d];
    for (i = 0; i < (INPUT_DIM-(d-1)); ++i){
        for (j = 0; j < NUM_BATCH; j++){
            for (k = 0; k < d; ++k){
                int shift = (j+(d-k-1)) % NUM_BATCH;
                if (k == 0){
                    for (int m = 0; m < d; m++){
                        if (j == 0){
                            if (indices[i] != padding){
                                forward_arr[(m*NUM_BATCH)+j] = arr[(int)indices[i+m]* NUM_BATCH + j];
                            } else {
                                forward_arr[(m*NUM_BATCH)+j] *= 0;
                            }
                        } else {
                            if (m == d-1){
                                if (indices[i] != padding){
                                    forward_arr[(m*NUM_BATCH)+j] = arr[(int)indices[i+m]* NUM_BATCH + j];
                                } else {
                                    forward_arr[(m*NUM_BATCH)+j] *= 0;
                                }
                            } else {
                                forward_arr[(m*NUM_BATCH)+j] = forward_arr[((m+1)*NUM_BATCH)+j];
                            }
                        }
                    }
                    actual = forward_arr[j];
                } else {
                    if (j == NUM_BATCH-1){
                       aux = shuffle(forward_arr[k*NUM_BATCH+j], (d-k-1));
                       for (int s = 0; s < (d-k-1); s++){
                          aux[s] = p[s];
                       }
                    } else if (j == 0){
                       aux = shuffle(forward_arr[k*NUM_BATCH+j], (d-k-1));
                      for (int s = 0; s < (d-k-1); s++){
                          p[s] = aux[s];
                          aux[s] = forward_arr[k*NUM_BATCH+NUM_BATCH-1][BATCH-(d-k-1)+s];
                      }
                    } else {
                       aux = shuffle(forward_arr[k*NUM_BATCH+j], (d-k-1));
                       for (int s = 0; s < (d-k-1); s++){
                          m[s] = aux[s];
                          aux[s] = p[s];
                          p[s] = m[s];
                       }
                   }
                   actual = actual * aux;
                }
              }
              enc[j] = enc[j] + actual;
        }
    }
    free(forward_arr);
    return enc;
}



f4si* ngram_forward(f4si* arr, float* indices, f4si* enc, const int d){
    int i, j, k;
    f4si aux;
    f4si *forward_arr = calloc(DIMENSIONS * d, sizeof(int));
    f4si actual;
    float m[d];
    float p[d];
    for (i = 0; i < (INPUT_DIM-(d-1)); ++i){
        for (j = 0; j < NUM_BATCH; j++){
            for (k = 0; k < d; ++k){
                int shift = (j+(d-k-1)) % NUM_BATCH;
                if (k == 0){
                    for (int m = 0; m < d; m++){
                        if (j == 0){
                            if (indices[i] != padding){
                                forward_arr[(m*NUM_BATCH)+j] = arr[(int)indices[i+m]* NUM_BATCH + j];
                            } else {
                                forward_arr[(m*NUM_BATCH)+j] *= 0;
                            }
                        } else {
                            if (m == d-1){
                                if (indices[i] != padding){
                                    forward_arr[(m*NUM_BATCH)+j] = arr[(int)indices[i+m]* NUM_BATCH + j];
                                } else {
                                    forward_arr[(m*NUM_BATCH)+j] *= 0;
                                }
                            } else {
                                forward_arr[(m*NUM_BATCH)+j] = forward_arr[((m+1)*NUM_BATCH)+j];
                            }
                        }
                    }
                    actual = forward_arr[j];
                } else {
                    if (j == NUM_BATCH-1){
                       aux = shuffle(forward_arr[k*NUM_BATCH+j], (d-k-1));
                       for (int s = 0; s < (d-k-1); s++){
                          aux[s] = p[s];
                       }
                    } else if (j == 0){
                       aux = shuffle(forward_arr[k*NUM_BATCH+j], (d-k-1));
                      for (int s = 0; s < (d-k-1); s++){
                          p[s] = aux[s];
                          aux[s] = forward_arr[k*NUM_BATCH+NUM_BATCH-1][BATCH-(d-k-1)+s];
                      }
                    } else {
                       aux = shuffle(forward_arr[k*NUM_BATCH+j], (d-k-1));
                       for (int s = 0; s < (d-k-1); s++){
                          m[s] = aux[s];
                          aux[s] = p[s];
                          p[s] = m[s];
                       }
                   }
                   actual = actual * aux;
                }
              }
              enc[j] = enc[j] + actual;
        }
    }
    free(forward_arr);
    return enc;
}



f4si* ngram_forward(f4si* arr, float* indices, f4si* enc, const int d){
    int i, j, k;
    f4si aux;
    f4si *forward_arr = calloc(DIMENSIONS * d, sizeof(int));
    f4si actual;
    for (i = 0; i < (INPUT_DIM-(d-1)); ++i){
        for (j = 0; j < NUM_BATCH; j++){
            for (k = 0; k < d; ++k){
                int shift = (j+(d-k-1)) % NUM_BATCH;
                if (k == 0){
                    for (int m = 0; m < d; m++){
                        if (j == 0){
                            if (indices[i] != padding){
                                forward_arr[(m*NUM_BATCH)+j] = arr[(int)indices[i+m]* NUM_BATCH + j];
                            } else {
                                forward_arr[(m*NUM_BATCH)+j] *= 0;
                            }
                        } else {
                            if (m == d-1){
                                if (indices[i] != padding){
                                    forward_arr[(m*NUM_BATCH)+j] = arr[(int)indices[i+m]* NUM_BATCH + j];
                                } else {
                                    forward_arr[(m*NUM_BATCH)+j] *= 0;
                                }
                            } else {
                                forward_arr[(m*NUM_BATCH)+j] = forward_arr[((m+1)*NUM_BATCH)+j];
                            }
                        }
                    }
                    actual = forward_arr[shift];
                } else {
                    actual = actual * forward_arr[(NUM_BATCH*(k))+shift];
                }
              }
              enc[j] = enc[j] + actual;
        }
    }
    free(forward_arr);
    return enc;
}


f4si* ngram(f4si* forward_arr, f4si* enc, const int d){
    int i, j, k;
    f4si aux;
    f4si actual;
    float m[d];
    float p[d];
    for (i = 0; i < (INPUT_DIM-(d-1)); ++i){
        for (j = 0; j < NUM_BATCH; j++){
            for (k = 0; k < d; ++k){
                int shift = (j+(d-k-1)) % NUM_BATCH;
                if (k == 0){
                    actual = forward_arr[NUM_BATCH*(i)+shift];
                } else {
                    if (j == NUM_BATCH-1){
                       aux = shuffle(forward_arr[(k+i)*NUM_BATCH+j], (d-k-1));
                       for (int s = 0; s < (d-k-1); s++){
                          aux[s] = p[s];
                       }
                    } else if (j == 0){
                       aux = shuffle(forward_arr[(k+i)*NUM_BATCH+j], (d-k-1));
                      for (int s = 0; s < (d-k-1); s++){
                          p[s] = aux[s];
                          aux[s] = forward_arr[(k+i)*NUM_BATCH+NUM_BATCH-1][BATCH-(d-k-1)+s];
                      }
                    } else {
                       aux = shuffle(forward_arr[(k+i)*NUM_BATCH+j], (d-k-1));
                       for (int s = 0; s < (d-k-1); s++){
                          m[s] = aux[s];
                          aux[s] = p[s];
                          p[s] = m[s];
                       }
                   }
                  actual = actual * aux;
                }
          }
           enc[j] = enc[j] + actual;
        }
    }
    return enc;
}



        f4si* ngram(f4si* forward_arr, f4si* enc, const int d){
            int i, j, k;
            f4si aux;
            f4si actual;
            for (i = 0; i < (INPUT_DIM-(d-1)); ++i){
                for (j = 0; j < NUM_BATCH; j++){
                    for (k = 0; k < d; ++k){
                        int shift = (j+(d-k-1)) % NUM_BATCH;
                        if (k == 0){
                            actual = forward_arr[NUM_BATCH*(i)+shift];
                        } else {
                            actual = actual * forward_arr[(NUM_BATCH*(i+k))+shift];
                        }
                  }
                   enc[j] = enc[j] + actual;
                }
            }
            return enc;
        }

        f4si* ngram_forward(f4si* arr, float* indices, f4si* enc, const int d){
            int i, j, k;
            f4si aux;
            f4si *forward_arr = calloc(DIMENSIONS * d, sizeof(int));
            f4si actual;
            for (i = 0; i < (INPUT_DIM-(d-1)); ++i){
                for (j = 0; j < NUM_BATCH; j++){
                    for (k = 0; k < d; ++k){
                        if (k == 0){
                            for (int m = 0; m < d; m++){
                                if (j == 0){
                                    if (indices[i] != padding){
                                        forward_arr[(m*NUM_BATCH)+j] = arr[(int)indices[i+m]* NUM_BATCH + j];
                                    } else {
                                        forward_arr[(m*NUM_BATCH)+j] *= 0;
                                    }
                                } else {
                                    if (m == d-1){
                                        if (indices[i] != padding){
                                            forward_arr[(m*NUM_BATCH)+j] = arr[(int)indices[i+m]* NUM_BATCH + j];
                                        } else {
                                            forward_arr[(m*NUM_BATCH)+j] *= 0;
                                        }
                                    } else {
                                        forward_arr[(m*NUM_BATCH)+j] = forward_arr[((m+1)*NUM_BATCH)+j];
                                    }
                                }
                            }
                            actual = forward_arr[k*NUM_BATCH+j];
                        } else {
                            int shift = (j-k) % NUM_BATCH;
                            actual = actual * forward_arr[NUM_BATCH*k+shift];
                        }
                      }
                      enc[j] = enc[j] + actual;
                }
            }
            free(forward_arr);
            return enc;
        }

        f4si* ngram_forward(f4si* arr, float* indices, f4si* enc, const int d){
            int i, j, k;
            f4si aux;
            f4si *forward_arr = calloc(DIMENSIONS * d, sizeof(int));
            f4si actual;
            for (i = 0; i < (INPUT_DIM-(d-1)); ++i){
                for (j = 0; j < NUM_BATCH; j++){
                    for (k = 0; k < d; ++k){
                        int shift = (j+(d-k-1)) % NUM_BATCH;
                        if (k == 0){
                            for (int m = 0; m < d; m++){
                                if (indices[i+m] != padding){
                                    forward_arr[(m*NUM_BATCH)+j] = arr[(int)indices[i+m]* NUM_BATCH + j];
                                } else {
                                    forward_arr[(m*NUM_BATCH)+j] *= 0;
                                }
                            }
                            actual = forward_arr[shift];
                        } else {
                            actual = actual * forward_arr[(NUM_BATCH*(k))+shift];
                        }
                      }
                      enc[j] = enc[j] + actual;
                }
            }
            free(forward_arr);
            return enc;
        }

        f4si* ngram_forward(f4si* arr, float* indices, f4si* enc, const int d){
            int i, j, k;
            f4si aux;
            f4si *forward_arr = calloc(DIMENSIONS * d, sizeof(int));
            f4si actual;
            for (i = 0; i < (INPUT_DIM-(d-1)); ++i){
                for (j = 0; j < NUM_BATCH; j++){
                    for (k = 0; k < d; ++k){
                        if (k == 0){
                            for (int m = 0; m < d; m++){
                                if (indices[i] != padding){
                                    forward_arr[(m*NUM_BATCH)+j] = arr[(int)indices[i+m]* NUM_BATCH + j];
                                } else {
                                    forward_arr[(m*NUM_BATCH)+j] *= 0;
                                }
                            }
                            actual = forward_arr[k*NUM_BATCH+j];
                        } else {
                            if (j < k){
                                aux = forward_arr[(k*NUM_BATCH)+NUM_BATCH-k+j];
                            } else {
                                aux = forward_arr[k*NUM_BATCH+j-k];
                            }
                            actual = actual * aux;
                        }
                      }
                       enc[j] = enc[j] + actual;
                }
            }
            free(forward_arr);
            return enc;
        }

        '''

        """Ngram a set of hypervectors together"""
        with open(self.name.lower() + '.c', 'a') as file:
            if self.vectorial:
                if self.performance:
                    file.write(
                '''
f4si* ngram(f4si* forward_arr, f4si* enc, const int d){
    int i, j, k;
    f4si aux;
    f4si actual;
    for (i = 0; i < (INPUT_DIM-(d-1)); ++i){
        for (j = 0; j < NUM_BATCH; j++){
            for (k = 0; k < d; ++k){
                int shift = (j+(d-k-1)) % NUM_BATCH;
                if (k == 0){
                    actual = forward_arr[NUM_BATCH*(i)+shift];
                } else {
                    actual = actual * forward_arr[(NUM_BATCH*(i+k))+shift];
                }
          }
           enc[j] = enc[j] + actual;
        }
    }
    return enc;
}
                '''
            )
                else:
                    file.write(
                     '''
f4si* ngram(f4si* forward_arr, f4si* enc, const int d){
    int i, j, k;
    f4si aux;
    f4si actual;
    float m[d];
    float p[d];
    for (i = 0; i < (INPUT_DIM-(d-1)); ++i){
        for (j = 0; j < NUM_BATCH; j++){
            for (k = 0; k < d; ++k){
                int shift = (j+(d-k-1)) % NUM_BATCH;
                if (k == 0){
                    actual = forward_arr[NUM_BATCH*(i)+shift];
                } else {
                    if (j == NUM_BATCH-1){
                       aux = shuffle(forward_arr[(k+i)*NUM_BATCH+j], (d-k-1));
                       for (int s = 0; s < (d-k-1); s++){
                          aux[s] = p[s];
                       }
                    } else if (j == 0){
                       aux = shuffle(forward_arr[(k+i)*NUM_BATCH+j], (d-k-1));
                      for (int s = 0; s < (d-k-1); s++){
                          p[s] = aux[s];
                          aux[s] = forward_arr[(k+i)*NUM_BATCH+NUM_BATCH-1][BATCH-(d-k-1)+s];
                      }
                    } else {
                       aux = shuffle(forward_arr[(k+i)*NUM_BATCH+j], (d-k-1));
                       for (int s = 0; s < (d-k-1); s++){
                          m[s] = aux[s];
                          aux[s] = p[s];
                          p[s] = m[s];
                       }
                   }
                  actual = actual * aux;
                }
          }
           enc[j] = enc[j] + actual;
        }
    }
    return enc;
}          
                     '''
                    )
            else:
                file.write(
                    '''
float* ngram(float* arr, float* enc, const int d){
    int i, j, k;

    float* res = calloc(DIMENSIONS * (INPUT_DIM-(d-1)), sizeof(float));
    float* sample = calloc(DIMENSIONS * (INPUT_DIM-(d-1)), sizeof(float));

    permute(arr, d-1, 0, (INPUT_DIM-(d-1)), res);
    for (i = 1; i < d; i++){
        permute(arr, d-i-1, i, (INPUT_DIM-(d-i-1)), sample);
        for (j = 0; j < (INPUT_DIM-(d-1)); ++j){
            for (int k = 0; k < DIMENSIONS; k++){
                res[(j*DIMENSIONS)+k] = res[(j*DIMENSIONS)+k] * sample[(j*DIMENSIONS)+k];
                enc[k] = enc[k] + res[(j*DIMENSIONS)+k];
            }
        }
    }

    free(sample);
    free(res);
    return enc;
}
'''
                )

    def generate_shuffle(self):
        """Ngram a set of hypervectors together"""
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(generate_shuffle(self.ngram_perm, self.vector_size))

    def ngram_forward(self):
        """Ngram a set of hypervectors together"""
        with open(self.name.lower() + '.c', 'a') as file:
            if self.vectorial:
                if self.performance:
                    file.write(
                '''
f4si* ngram_forward(f4si* arr, float* indices, f4si* enc, const int d){
    int i, j, k;
    f4si aux;
    f4si *forward_arr = calloc(DIMENSIONS * d, sizeof(int));
    f4si actual;
    for (i = 0; i < (INPUT_DIM-(d-1)); ++i){
        for (j = 0; j < NUM_BATCH; j++){
            for (k = 0; k < d; ++k){
                int shift = (j+(d-k-1)) % NUM_BATCH;
                if (k == 0){
                    for (int m = 0; m < d; m++){
                        if (j == 0){
                            if (indices[i] != padding){
                                forward_arr[(m*NUM_BATCH)+j] = arr[(int)indices[i+m]* NUM_BATCH + j];
                            } else {
                                forward_arr[(m*NUM_BATCH)+j] *= 0;
                            }
                        } else {
                            if (m == d-1){
                                if (indices[i] != padding){
                                    forward_arr[(m*NUM_BATCH)+j] = arr[(int)indices[i+m]* NUM_BATCH + j];
                                } else {
                                    forward_arr[(m*NUM_BATCH)+j] *= 0;
                                }
                            } else {
                                forward_arr[(m*NUM_BATCH)+j] = forward_arr[((m+1)*NUM_BATCH)+j];
                            }
                        }
                    }
                    actual = forward_arr[shift];
                } else {
                    actual = actual * forward_arr[(NUM_BATCH*(k))+shift];
                }
              }
              enc[j] = enc[j] + actual;
        }
    }
    free(forward_arr);
    return enc;
}
                '''
            )
                else:
                    file.write(
                        '''
f4si* ngram_forward(f4si* arr, float* indices, f4si* enc, const int d){
    int i, j, k;
    f4si aux;
    f4si *forward_arr = calloc(DIMENSIONS * d, sizeof(int));
    f4si actual;
    float m[d];
    float p[d];
    for (i = 0; i < (INPUT_DIM-(d-1)); ++i){
        for (j = 0; j < NUM_BATCH; j++){
            for (k = 0; k < d; ++k){
                int shift = (j+(d-k-1)) % NUM_BATCH;
                if (k == 0){
                    for (int m = 0; m < d; m++){
                        if (j == 0){
                            if (indices[i] != padding){
                                forward_arr[(m*NUM_BATCH)+j] = arr[(int)indices[i+m]* NUM_BATCH + j];
                            } else {
                                forward_arr[(m*NUM_BATCH)+j] *= 0;
                            }
                        } else {
                            if (m == d-1){
                                if (indices[i] != padding){
                                    forward_arr[(m*NUM_BATCH)+j] = arr[(int)indices[i+m]* NUM_BATCH + j];
                                } else {
                                    forward_arr[(m*NUM_BATCH)+j] *= 0;
                                }
                            } else {
                                forward_arr[(m*NUM_BATCH)+j] = forward_arr[((m+1)*NUM_BATCH)+j];
                            }
                        }
                    }
                    actual = forward_arr[j];
                } else {
                    if (j == NUM_BATCH-1){
                       aux = shuffle(forward_arr[k*NUM_BATCH+j], (d-k-1));
                       for (int s = 0; s < (d-k-1); s++){
                          aux[s] = p[s];
                       }
                    } else if (j == 0){
                       aux = shuffle(forward_arr[k*NUM_BATCH+j], (d-k-1));
                      for (int s = 0; s < (d-k-1); s++){
                          p[s] = aux[s];
                          aux[s] = forward_arr[k*NUM_BATCH+NUM_BATCH-1][BATCH-(d-k-1)+s];
                      }
                    } else {
                       aux = shuffle(forward_arr[k*NUM_BATCH+j], (d-k-1));
                       for (int s = 0; s < (d-k-1); s++){
                          m[s] = aux[s];
                          aux[s] = p[s];
                          p[s] = m[s];
                       }
                   }
                   actual = actual * aux;
                }
              }
              enc[j] = enc[j] + actual;
        }
    }
    free(forward_arr);
    return enc;
}
                        '''
                    )
            else:
                file.write(
                    '''
float* ngram_forward(float* arr, float* indices, float* enc, const int d){
    int i, j, k;
    float* forw = calloc(DIMENSIONS * INPUT_DIM, sizeof(float));
    forw = forward(arr,indices,forw);
    float* res = calloc(DIMENSIONS * (INPUT_DIM-(d-1)), sizeof(float));
    float* sample = calloc(DIMENSIONS * (INPUT_DIM-(d-1)), sizeof(float));

    permute(forw, d-1, 0, (INPUT_DIM-(d-1)), res);
    for (i = 1; i < d; i++){
        permute(forw, d-i-1, i, (INPUT_DIM-(d-i-1)), sample);
        for (j = 0; j < (INPUT_DIM-(d-1)); ++j){
            for (int k = 0; k < DIMENSIONS; k++){
                res[(j*DIMENSIONS)+k] = res[(j*DIMENSIONS)+k] * sample[(j*DIMENSIONS)+k];
                enc[k] = enc[k] + res[(j*DIMENSIONS)+k];
            }
        }
    }

    free(forw);
    free(sample);
    free(res);
    return enc;
}
'''
                )

    def multiset(self):
        """Bundles two hypervectors together"""
        with open(self.name.lower() + '.c', 'a') as file:
            if self.vectorial:
                file.write(
                '''
f4si *multiset(f4si *a){
    int i, j;
    for(i = 1; i < INPUT_DIM; i++){
        for(j = 0; j < NUM_BATCH; ++j){
            a[j] += a[(NUM_BATCH * i) + j];
        }
    }
    return a;
}
                '''
            )
            else:
                file.write(
                    '''
float *multiset(float *a){
    int i, j;
    for(i = 1; i < INPUT_DIM; i++){
        for(j = 0; j < DIMENSIONS; ++j){
            a[j] += a[(DIMENSIONS * i) + j];
        }
    }
    return a;
}
                    '''
                )

    def multiset_multibind_forward(self):
        """Bundles two hypervectors together"""
        with open(self.name.lower() + '.c', 'a') as file:
            if self.vectorial:
                file.write(
                '''
f4si *multiset_multibind_forward(f4si *a, f4si *b, float* indices, f4si* enc){
    int i, j;
    for(i = 0; i < INPUT_DIM; ++i){
        for(j = 0; j < NUM_BATCH; j++){
            if (indices[i] != padding){
                enc[j] += a[(NUM_BATCH * i) + j] * b[(int)indices[i]* NUM_BATCH + j];
            } else {
                enc[j] *= a[(NUM_BATCH * i) + j] * 0;
            }
        }
    }
    return enc;
}
                '''
            )
            else:
                file.write(
                    '''
float *multiset_multibind_forward(float *a, float *b, float* indices, float* enc){
    int i, j;
    for(i = 0; i < INPUT_DIM; ++i){
        for(j = 0; j < DIMENSIONS; j++){
            enc[j] += a[(DIMENSIONS * i) + j] * b[(int)indices[i]* DIMENSIONS + j];
        }
    }
    return enc;
}
                '''
                )

    def multiset_multibind(self):
        """Bundles two hypervectors together"""
        with open(self.name.lower() + '.c', 'a') as file:
            if self.vectorial:
                file.write(
                '''
f4si *multiset_multibind(f4si *a, f4si *b, f4si* enc){
    int i, j;
    for(i = 0; i < INPUT_DIM; ++i){
        for(j = 0; j < NUM_BATCH; j++){
             enc[j] += a[(NUM_BATCH * i) + j] * b[NUM_BATCH + j];
        }
    }
    return enc;
}
                '''
            )
            else:
                file.write(
                '''
float *multiset_multibind(float *a, float *b, float* enc){
int i, j;
for(i = 0; i < INPUT_DIM; ++i){
    for(j = 0; j < DIMENSIONS; j++){
         enc[j] += a[(DIMENSIONS * i) + j] * b[DIMENSIONS + j];
    }
}
return enc;
}
            '''
            )

    def multiset_forward(self):
        """Bundles two hypervectors together"""
        with open(self.name.lower() + '.c', 'a') as file:
            if self.vectorial:
                file.write(
                '''
f4si *multiset_forward(f4si *a, float* indices){
    int i, j;
    for(i = 0; i < INPUT_DIM; i++){
        for(j = 0; j < NUM_BATCH; ++j){
            if (indices[i] != padding){
                a[j] += a[(int)indices[i] * DIMENSIONS + j];
            } else {
                a[j] += a[(int)indices[i] * DIMENSIONS + j]*0;
            }
        }
    }
    return a;
}
                '''
            )
            else:
                file.write(
                    '''
float *multiset_forward(float *a, float* indices){
    int i, j;
    for(i = 0; i < INPUT_DIM; i++){
        for(j = 0; j < DIMENSIONS; ++j){
            a[j] += a[(int)indices[i] * i + j];
        }
    }
    return a;
}
                    '''
                )

    def forward(self):
        with open(self.name.lower() + '.c', 'a') as file:
            if self.vectorial:
                file.write(
                    '''
f4si *forward(f4si *a, float* indices, f4si* enc){
    int i, j;
    for(i = 0; i < INPUT_DIM; ++i){
        for(j = 0; j < NUM_BATCH; j++){
            if (indices[i] != padding){
                enc[(NUM_BATCH * i) + j] = a[(int)indices[i]* NUM_BATCH + j];
            } else {
                enc[(NUM_BATCH * i) + j] = a[(int)indices[i]* NUM_BATCH + j] * 0;
            }
        }
    }
    return enc;
}              
                        ''')
            else:
                file.write(
                        '''
float* forward(float *a, float* indices, float* enc){
    int i, j;
    for(i = 0; i < INPUT_DIM; ++i){
        for(j = 0; j < DIMENSIONS; j++){
           if (indices[i] != padding){
               enc[(DIMENSIONS * i) + j] = a[((int)indices[i]* DIMENSIONS) + j];
            } else {
                enc[(DIMENSIONS * i) + j] *= 0;
            }
        }
    }
    return enc;
}  
                        ''')

    def permute(self):
        '''
        f4si *permute(f4si* arr, int d, int ini, int fi)
        {
            int i, j, k;
            f4si *res = calloc(DIMENSIONS*(fi-ini), sizeof(int));
            for (i = 0; i < (fi-ini); ++i){
                for (j = 0; j < NUM_BATCH; j++){
                    if (j < d){
                        res[(i*NUM_BATCH)+j] = arr[(i*NUM_BATCH)+NUM_BATCH-d+j];
                    } else {
                        res[(i*NUM_BATCH)+j] = arr[(i*NUM_BATCH)+j+d];
                    }
                }
            }
            free(arr);
            return res;
        }


        '''

        if self.vectorial:
            if self.performance:
                with open(self.name.lower() + '.c', 'a') as file:
                    file.write(
                '''
f4si *permute(f4si* arr, int dd, int ini, int fi)
{
    int k, j, i;
    float last;
    f4si * res = malloc(VECTOR_SIZE*(dd)* sizeof(int));
    for (i = ini; i < fi; ++i){
      for (j = 0; j < NUM_BATCH; j++){
         for(k = 0; k < BATCH; k++){
            if ((BATCH*j)+k+dd < ((BATCH*NUM_BATCH))){
                if (k+dd >= BATCH){
                    int num = (k+dd) % BATCH;
                    arr[(i-ini)*NUM_BATCH+j+1][num] = arr[i*NUM_BATCH+j][k];
                    if (k < dd){
                        res[0][k] = arr[i*NUM_BATCH+j][k];
                    }
                } else {
                    arr[(i-ini)*NUM_BATCH+j][k+dd] = res[0][NUM_BATCH-k+dd];
                }
            } else {
                int num = (k+dd) % BATCH;
                arr[(i-ini)*NUM_BATCH+j-1][num] = arr[i*NUM_BATCH+j][k];
            }
         }
      }
    }
    return arr;
}
                ''')

            for i in self.permutes:
                with open(self.name.lower() + '.c', 'a') as file:
                    file.write(
                            '''
 f4si *permute'''+str(i)+'''(f4si* arr, int dd, int ini, int fi)
{

    int k, j, i;
    float n[dd];
    float p[dd];

    f4si * res = calloc(DIMENSIONS*(fi-ini), sizeof(int));
    for (i = ini; i < fi; ++i){
      for (j = 0; j < NUM_BATCH; j++){
       if (j == NUM_BATCH-1){
           res[i*NUM_BATCH+j] = __builtin_shufflevector(arr[i*NUM_BATCH+j],arr[i*NUM_BATCH+j]'''+generate(self.vector_size/4,i)+''');
           for (k = 0; k < dd; k++){
               res[i*NUM_BATCH+j][k] = p[k];
           }
       } else if (j == 0){
           res[i*NUM_BATCH+j] = __builtin_shufflevector(arr[i*NUM_BATCH+j],arr[i*NUM_BATCH+j]'''+generate(self.vector_size/4,i)+''');
           for (k = 0; k < dd; k++){
               p[k] = res[i*NUM_BATCH+j][k];
           }
       } else {
           res[i*NUM_BATCH+j] = __builtin_shufflevector(arr[i*NUM_BATCH+j],arr[i*NUM_BATCH+j]'''+generate(self.vector_size/4,i)+''');
           for (k = 0; k < dd; k++){
               n[k] = res[i*NUM_BATCH+j][k];
               res[i*NUM_BATCH+j][k] = p[k];
               p[k] = n[k];
               n[k] = p[k];
           }
       }
      }
    }
    free(arr);
    return res;
}
                    '''

                )
        else:
            with open(self.name.lower() + '.c', 'a') as file:
                file.write(
                        '''
void permute(float* arr, int d, int ini, int fi, float * result)
{
    for (int i = ini; i < fi; i++){
        if (d == 0){
           for (int j = 0; j < DIMENSIONS; j++){
                result[((i-ini)*DIMENSIONS)+j] = arr[(i*DIMENSIONS)+j];
            }   
        } else {
           for (int j = 0; j < DIMENSIONS-d; j++){
                result[((i-ini)*DIMENSIONS)+j+d] = arr[(i*DIMENSIONS)+j];
            }
            for (int j = 0; j < d; j++){
                result[((i-ini)*DIMENSIONS)+j] = arr[(i*DIMENSIONS)+DIMENSIONS-d+j];
            }
        }
    }
}
                        '''
                    )

    def define_hdc_functions(self):
        self.define_random_hv()
        self.define_level_hv()
        self.multibind()
        self.multibind_forward()
        self.multiset()
        self.multiset_forward()
        self.multiset_multibind()
        self.multiset_multibind_forward()
        self.forward()
        self.permute()

        if self.ngram_perm != None:
            if self.vectorial:
                self.generate_shuffle()

            self.ngram()
            self.ngram_forward()

        self.define_encoding_function()

    def define_random_hv(self):
        with open(self.name.lower() + '.c', 'a') as file:
            if self.vectorial:
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
            else:
                file.write(
                    '''
float *random_hv(int size){
   float *arr = calloc(size * DIMENSIONS, sizeof(float));
   int P = 50;
   int i, j, k;
   for (i = 0; i < size; i++){
      for (j = 0; j < DIMENSIONS; j++){
        arr[(i*DIMENSIONS)+j] = rand() % 100 > P ? 1 : -1;
      }
   }
   return arr;
}
                        '''
                    )

    def define_level_hv(self):
        with open(self.name.lower() + '.c', 'a') as file:
            if self.vectorial:
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
            else:
                file.write(
                    '''
float *level_hv(int levels){
    int levels_per_span = levels-1;
    int span = 1;
    float *span_hv = random_hv(span+1);
    float *threshold_hv = random_vector(span,0,1);
    float *hv = calloc(levels * DIMENSIONS, sizeof(float));
    int i, j, k;
    for(i = 0; i < levels; i++){
        float t = 1 - ((float)i / levels_per_span);
        for(j = 0; j < DIMENSIONS; j++){
            if((t > threshold_hv[j] || i == 0) && i != levels-1){
                hv[i*DIMENSIONS+j] = span_hv[0*DIMENSIONS+j];
            } else {
                hv[i*DIMENSIONS+j] = span_hv[1*DIMENSIONS+j];
            }   
        }
    }
    return hv;
}
                        '''
                )

    def define_circular_hv(self):
        with open(self.name.lower() + '.c', 'a') as file:
            if self.vectorial:
                file.write(
                    '''                 
f4si *bind_inverse(f4si *a, f4si *b){
    int k, j;
    f4si * enc = calloc(DIMENSIONS, sizeof(int));
    for(j = 0; j < NUM_BATCH; j++){
        enc[j] = a[j] * -b[j];
    }
    return enc;
}
void print_matrix_d(f4si* arr, int rows){
    int i, j;
    for (int i = 0; i < rows; i++){
        for(int j = 0; j < NUM_BATCH; j++){
            for(int k = 0; k < BATCH; k++){
                printf("%f ", arr[i * NUM_BATCH+j][k]);
            }
        }
        printf("\n");
    }
    printf("\n");
}

f4si *circular_hv(int levels){
    int levels_per_span = levels;
    int span = 1;
    f4si *span_hv = random_hv(span+1);
    f4si *threshold_v = random_vector(span,0,1);
    f4si *hv = calloc(levels * DIMENSIONS, sizeof(float));
    f4si *temp_hv = calloc(DIMENSIONS, sizeof(float));
    f4si* mutation_hv = calloc(DIMENSIONS, sizeof(float));


    for(int j = 0; j < NUM_BATCH; j++){
        mutation_hv[j] = span_hv[j];
        hv[j] = span_hv[j];
    }

    f4si** mutation_history = (f4si**)malloc(sizeof(f4si*) * levels);
    for (int i = 1; i <= levels; i++) {
        int span_idx = floor(i / levels_per_span);

        if (abs(i - levels_per_span * span_idx) < 1e-12) {
            for(int j = 0; j < NUM_BATCH; j++){
                temp_hv[j] = span_hv[j];
            }

        } else {
            f4si* span_start_hv = calloc(DIMENSIONS, sizeof(float));
            f4si* span_end_hv = calloc(DIMENSIONS, sizeof(float));
            for(int j = 0; j < NUM_BATCH; j++){
                span_start_hv[j] = span_hv[span_idx * NUM_BATCH+j];
                span_end_hv[j] = span_hv[(span_idx+1) * NUM_BATCH+j];
            }
            float level_within_span = fmod(i, levels_per_span);
            float t = 1 - (level_within_span / levels_per_span);

            for(int j = 0; j < NUM_BATCH; j++){
                for(int k = 0; k < BATCH; k++){
                    temp_hv[j][k] = threshold_v[(span_idx * NUM_BATCH + j)][k] ? span_start_hv[j][k] : span_end_hv[j][k];
                }
            }
        }
        mutation_history[i - 1] = bind_inverse(temp_hv, mutation_hv);

        for(int j = 0; j < NUM_BATCH; j++){
            mutation_hv[j] = temp_hv[j];
        }
        if (i % 2 == 0) {
            for(int j = 0; j < NUM_BATCH; j++){
                int idx = (int)floor(i / 2) * NUM_BATCH + j;
                hv[idx] = mutation_hv[j];
            }
        }

    }

    for (int i = levels + 1; i < levels * 2 - 1; i++) {
        f4si* mut = mutation_history[i - levels - 1];

        mutation_hv = bind_inverse(mutation_hv, mut);

        if (i % 2 == 0) {
            for(int j = 0; j < NUM_BATCH; j++){
                int idx = (int) floor(i / 2) * NUM_BATCH + j;
                hv[idx] = mutation_hv[j];
            }

        }
        free(mut);
    }
    free(mutation_history);
    free(mutation_hv);
    free(threshold_v);
    free(span_hv);
    return hv;
}
                        '''
                )
            else:
                file.write(
                    '''

float *bind_inverse(float *a, float *b){
    int i, j;
    float *enc = (float *)calloc(DIMENSIONS, sizeof(int));
    for(j = 0; j < DIMENSIONS; j++){
         enc[j] = a[j] * -b[j];
    }
    return enc;
}

float *circular_hv(int levels){
    int levels_per_span = levels;
    int span = 1;
    float *span_hv = random_hv(span+1);
    float *threshold_v = random_vector(span,0,1);
    float *hv = calloc(levels * DIMENSIONS, sizeof(float));
    for (int i = 0; i < DIMENSIONS; i++) {
        hv[i] = span_hv[i];
    }

    float *temp_hv = calloc(DIMENSIONS, sizeof(float));

    float* mutation_hv = calloc(DIMENSIONS, sizeof(float));
    for (int i = 0; i < DIMENSIONS; i++) {
        mutation_hv[i] = span_hv[i];
    }
    float** mutation_history = (float**)malloc(sizeof(float*) * levels);
    for (int i = 1; i <= levels; i++) {
        int span_idx = floor(i / levels_per_span);

        if (abs(i - levels_per_span * span_idx) < 1e-12) {
            for (int j = 0; j < DIMENSIONS; j++) {
                temp_hv[j] = span_hv[span_idx * DIMENSIONS + j];
            }
        } else {
            float* span_start_hv = calloc(DIMENSIONS, sizeof(float));
            float* span_end_hv = calloc(DIMENSIONS, sizeof(float));

            for (int j = 0; j < DIMENSIONS; j++) {
                span_start_hv[j] = span_hv[(span_idx) * DIMENSIONS + j];
                span_end_hv[j] = span_hv[(span_idx+1) * DIMENSIONS + j];
            }

            float level_within_span = fmod(i, levels_per_span);
            float t = 1 - (level_within_span / levels_per_span);

            for (int j = 0; j < DIMENSIONS; j++) {
                temp_hv[j] = ((threshold_v[(span_idx * DIMENSIONS) + j] < t) ? span_start_hv[j] : span_end_hv[j]);
            }
        }
        // mutation_history[i - 1] = (float*)malloc(sizeof(float) * DIMENSIONS);
        mutation_history[i - 1] = bind_inverse(temp_hv, mutation_hv);

        for (int j = 0; j < DIMENSIONS; j++) {
            mutation_hv[j] = temp_hv[j];
        }

        if (i % 2 == 0) {
            for (int j = 0; j < DIMENSIONS; j++) {
                int idx = floor(i / 2) * DIMENSIONS + j;
                hv[idx] = mutation_hv[j];
            }
        }
    }

    for (int i = levels + 1; i < levels * 2 - 1; i++) {
        float* mut = mutation_history[i - levels - 1];

        mutation_hv = bind_inverse(mutation_hv, mut);

        if (i % 2 == 0) {
            for (int j = 0; j < DIMENSIONS; j++) {
                int idx = floor(i / 2) * DIMENSIONS + j;
                hv[idx] = mutation_hv[j];
            }
        }

        free(mut);
    }

    free(mutation_history);
    free(mutation_hv);
    free(threshold_v);
    free(span_hv);
    return hv;
}
                        '''
                )


    def define_thermometer_hv(self):
        with open(self.name.lower() + '.c', 'a') as file:
            if self.vectorial:
                file.write(
                    '''                 
float *thermometer_hv(int levels){
    int step = 0;
    if (levels > 0){
        step = (int) floor(DIMENSIONS / (levels-1));
    }
    float *hv = calloc(levels * DIMENSIONS, sizeof(float));

    int i, j, k;
    int current_step = step;
    for(i = 0; i < levels; i++){
        for(j = 0; j < DIMENSIONS; j++){ 
            if (j < step){
                hv[i*DIMENSIONS+j] = 1;
            } else {
                hv[i*DIMENSIONS+j] = -1;
            } 
        }
        current_step += step;
    }
    return hv;
}
                            '''
                    )
            else:
                file.write(
                        '''
f4si *thermometer_hv(int levels){
    int step = 0;
    if (levels > 0){
        step = (int) floor(DIMENSIONS / (levels-1));
    }
    f4si *hv = calloc(levels * DIMENSIONS, sizeof(float));

    int i, j, k;
    int current_step = step;
    for(i = 0; i < levels; i++){
        for(j = 0; j < NUM_BATCH; j++){
            for(k = 0; k < BATCH; k++){
                if ((j*NUM_BATCH) + k < step){
                    hv[i*NUM_BATCH+j][k] = 1;
                } else {
                    hv[i*NUM_BATCH+j][k] = -1;
                }
             }
        }
        current_step += step;
    }
    return hv;
}
                        '''
                    )


    def define_encoding_function(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(self.encoding_fun)

    def define_encoding_train(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
void encode_function_train(float* train_data, int label){
    for (int i = 0; i < NUM_THREADS; i++) {
        struct EncodeTaskTrain *task = (struct EncodeTaskTrain *)calloc(1, sizeof(struct EncodeTaskTrain));
        task -> split_start = i*SPLIT_SIZE;
        task -> data = train_data;
        task -> label = label;
        mt_add_job(pool, &encode_fun_train, task);
    }
}
                ''')

    def define_train_and_test(self):
        self.define_train_loop()
        self.define_test_loop()

    def define_train_loop(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
void train_loop(){
    int i;
    for(i = 0; i < TRAIN; i++){
        struct Task *task = (struct Task *)calloc(1,sizeof(struct Task));
        task -> data = load_data_next_line(train_data);
        task -> label = load_labels_next_line(train_labels);
        mt_add_job(pool, &encode_train_task, task);
    }
    mt_join(pool);
    normalize();
}
                    '''
            )

    def define_test_loop(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
float test_loop(){
    int i;
    for(i = 0; i < TEST; i++){
        struct Task *task = (struct Task *)calloc(1,sizeof(struct Task));
        task -> data = load_data_next_line(test_data);
        task -> label = load_labels_next_line(test_labels);
        mt_add_job(pool, &encode_test_task, task);
    }
    mt_join(pool);
    return CORRECT_PREDICTIONS/(float)TEST;
}
                    '''
            )

    def general_main(self):
        with open(self.name.lower() + '.c', 'a') as file:
            file.write(
                '''
int main(int argc, char **argv) {
    srand(time(NULL));
    '''
                +
                str(self.define_embeddings())
                +
                '''
    pool = mt_create_pool(NUM_THREADS);
    weights();
    prepare_to_load_data(argv);
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
    printf("''' + self.basic_name + ''',%d,%f,%f", DIMENSIONS,elapsed, acc);
                    '''
                )
            else:
                file.write(
                    '''
        printf("''' + self.basic_name + ''',%d,%f", DIMENSIONS, acc);
                    '''
                )

            file.write(
                '''
}              
                '''
            )





'''
f4si *permute(f4si* arr, int d, int ini, int fi)
{
    int i, j, k;
    f4si *res = calloc(DIMENSIONS*(fi-ini), sizeof(int));
    for (i = 0; i < (fi-ini); ++i){
        for (j = 0; j < NUM_BATCH; j++){
            int shift = (j+d) % NUM_BATCH;
            res[(i*NUM_BATCH)+j] = arr[((i+ini)*NUM_BATCH)+shift];
        }
    }
    //free(arr);
    return res;
}


f4si* ngram(f4si* arr, f4si* enc, const int d){
    int i, j, k;

    //float* res = calloc(DIMENSIONS * (INPUT_DIM-(d-1)), sizeof(float));
    f4si* sample = calloc(DIMENSIONS * (INPUT_DIM-(d-1)), sizeof(float));
    f4si* ng = calloc(DIMENSIONS * (INPUT_DIM-(d-1)), sizeof(float));

    ng = permute(arr, d-1, 0, (INPUT_DIM-(d-1)));
    for (i = 1; i < d; i++){
        sample = permute(arr, d-i-1, i, (INPUT_DIM-(d-i-1)));
        ng = multibind(ng,sample,(INPUT_DIM-(d-1)));
    }

    enc = multiset(ng, (INPUT_DIM-(d-1)));
    free(sample);
    //free(ng);
    return enc;
}
'''
