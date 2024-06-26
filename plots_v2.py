import pandas as pd
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")
folder = 'results/'
# file_hdcc = folder + 'opengpu_num_threads_20_vector_size_hdcc_08_01_2023_00:03:30'
file_hdcc = folder + 'mac_num_threads_4_vector_size_hdcc_23_01_2023_14:27:17'
file_torchhd = folder + 'mac_torchhd_21_01_2023_10:16:09'

file_torchhd_opengpu = folder + 'opengpu_torchhd_22_01_2023_09:42:05'
file_hdcc_opengpu = folder + 'opengpu_num_threads_20_vector_size_hdcc_23_01_2023_16:18:55'

file_hdcc_openlab = folder + 'openlab_num_threads_20_vector_size_hdcc_24_01_2023_08:50:02'
file_torchhd_openlab = folder + 'openlab_torchhd_21_01_2023_11:05:57'

file_hdcc_ubuntu = folder + 'ubuntu_num_threads_4_vector_size_hdcc_24_01_2023_01:25:49'
file_torchhd_ubuntu = folder + 'ubuntu_torchhd_21_01_2023_20:13:18'
# file_torchhd = folder + 'opengpu_torchhd_08_01_2023_07:21:50'

machines_names = ['ARM','Intel1','Intel2','Intel3']
dataset_hdcc = [pd.read_csv(file_hdcc), pd.read_csv(file_hdcc_openlab), pd.read_csv(file_hdcc_opengpu), pd.read_csv(file_hdcc_ubuntu)]
dataset_torchhd = [pd.read_csv(file_torchhd), pd.read_csv(file_torchhd_openlab), pd.read_csv(file_torchhd_opengpu), pd.read_csv(file_torchhd_ubuntu)]

first = True
machines = 4
names = ['Isolet','Mnist','Emg','Lang recognition']
fig, axs = plt.subplots(3, 4)
key = ['voicehd','mnist','emgppp','languages']
for j in range(len(key)):
    for i in range(machines):
        time_hdc = dataset_hdcc[i][:][dataset_hdcc[i].Application == key[j]][["Dimensions", "Application", "Time"]].groupby('Dimensions').mean().reset_index()
        time_hdc['Tool'] = 'HDCC'
        time_torchhd = dataset_torchhd[i][:][dataset_torchhd[i].Application == key[j]][["Dimensions", "Application", "Time"]].groupby('Dimensions').mean().reset_index()
        time_torchhd['Tool'] = 'TORCHHD'

        accuracy_hdc = dataset_hdcc[i][:][dataset_hdcc[i].Application == key[j]][["Dimensions", "Application", "Accuracy"]].groupby('Dimensions').mean().reset_index()
        accuracy_hdc['Tool'] = 'HDCC'
        accuracy_torchhd = dataset_torchhd[i][:][dataset_torchhd[i].Application == key[j]][
            ["Dimensions", "Application", "Accuracy"]].groupby('Dimensions').mean().reset_index()
        accuracy_torchhd['Tool'] = 'TORCHHD'

        memory_hdc = dataset_hdcc[i][:][dataset_hdcc[i].Application == key[j]][["Dimensions", "Application", "Memory"]].groupby('Dimensions').mean().reset_index()
        memory_hdc['Tool'] = 'HDCC'
        memory_torchhd = dataset_torchhd[i][:][dataset_torchhd[i].Application == key[j]][
            ["Dimensions", "Application", "Memory"]].groupby('Dimensions').mean().reset_index()


        memory_torchhd['Tool'] = 'TORCHHD'
        # axs[1,i].set_ylim(ymin=0.6)
        axs[0, j].plot(time_hdc['Dimensions'], time_hdc['Time'], label='HDCC '+machines_names[i])
        axs[0, j].plot(time_torchhd['Dimensions'], time_torchhd['Time'], label='TorchHD '+machines_names[i])
        axs[1, j].plot(accuracy_hdc['Dimensions'], accuracy_hdc['Accuracy'], label='HDCC '+machines_names[i])
        axs[1, j].plot(accuracy_torchhd['Dimensions'], accuracy_torchhd['Accuracy'], label='TorchHD '+machines_names[i])
        axs[2, j].plot(memory_hdc['Dimensions'], memory_hdc['Memory'], label='HDCC '+machines_names[i])
        axs[2, j].plot(memory_torchhd['Dimensions'], memory_torchhd['Memory'], label='TorchHD '+machines_names[i])

    axs[0, j].set_title(label=names[j]+'\n\nTime')
    axs[0, j].set_xlabel('Dimensions')
    axs[0, j].set_ylabel('Time (s)')

    axs[1, j].set_title(label='Accuracy')
    axs[1, j].set_xlabel('Dimensions')
    axs[1, j].set_ylabel('Accuracy')

    axs[2, j].set_title(label='Peak memory')
    axs[2, j].set_xlabel('Dimensions')
    axs[2, j].set_ylabel('Memory (bytes)')


plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
plt.show()
