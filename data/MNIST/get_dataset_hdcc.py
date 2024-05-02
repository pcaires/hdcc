import mnist
import numpy as np

mnist.temporary_dir = lambda: "raw"

_train_i = mnist.train_images()
train_i = _train_i.reshape((_train_i.shape[0],-1))

_test_i = mnist.test_images()
test_i = _test_i.reshape((_test_i.shape[0],-1))

train_l = mnist.train_labels()
test_l = mnist.test_labels()

np.savetxt("mnist_train_data",train_i,delimiter=",",fmt='%d')
np.savetxt("mnist_test_data",test_i,delimiter=",",fmt='%d')
np.savetxt("mnist_train_labels",train_l,fmt='%d')
np.savetxt("mnist_test_labels",test_l,fmt='%d')