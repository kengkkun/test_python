# import library
from os import listdir
from os.path import isdir, join
import random
import librosa
import numpy as np
import matplotlib.pyplot as plt
import python_speech_features
import pandas as pd
from tqdm import tqdm


dataset_path = 'C:/Users/waeng/Desktop/audio_classification/data/train/'
for name in listdir(dataset_path):
    if isdir(join(dataset_path, name)):
        # print(name)
        pass

# Created an all targets list
all_targets = [name for name in listdir(
    dataset_path) if isdir(join(dataset_path, name))]
# print(all_targets)

# See how many files are in each
num_samples = 0
for target in all_targets:
    # print(len(listdir(join(dataset_path, target))))
    num_samples += len(listdir(join(dataset_path, target)))
# print('Total samples:', num_samples)


# Settings
target_list = all_targets
feature_sets_file = 'all_targets_mfcc_sets.npz'
perc_keep_samples = 1.0  # 1.0 is keep all samples
val_ratio = 0.3
test_ratio = 0.1
sample_rate = 8000
num_mfcc = 16
len_mfcc = 16
threshold = 0.1


# Create list of filenames along with ground truth vector (y)
filenames = []
y = []
for index, target in enumerate(target_list):
    # print(join(dataset_path, target))
    filenames.append(listdir(join(dataset_path, target)))
    y.append(np.ones(len(filenames[index])) * index)


# Flatten filename and y vectors
filenames = [item for sublist in filenames for item in sublist]
y = [item for sublist in y for item in sublist]


# Associate filenames with true output and shuffle
filenames_y = list(zip(filenames, y))
random.shuffle(filenames_y)
filenames, y = zip(*filenames_y)


# Only keep the specified number of samples (shorter extraction/training)
print('all file name : ', len(filenames))
filenames = filenames[:int(len(filenames) * perc_keep_samples)]
print('keep file name : ', len(filenames))

# Calculate validation and test set sizes
val_set_size = int(len(filenames) * val_ratio)
test_set_size = int(len(filenames) * test_ratio)

# Break dataset apart into train, validation, and test sets
filenames_val = filenames[:val_set_size]
filenames_test = filenames[val_set_size:(val_set_size + test_set_size)]
filenames_train = filenames[(val_set_size + test_set_size):]

# Break y apart into train, validation, and test sets
y_orig_val = y[:val_set_size]
y_orig_test = y[val_set_size:(val_set_size + test_set_size)]
y_orig_train = y[(val_set_size + test_set_size):]


def envelope(y, rate, threshold):
    mask = []
    y = pd.Series(y).apply(np.abs)
    y_mean = y.rolling(window=int(rate/20),
                       min_periods=1,
                       center=True).max()
    for mean in y_mean:
        if mean > threshold:
            mask.append(True)
        else:
            mask.append(False)
    return mask, y_mean


# Function: Create MFCC from given path
def calc_mfcc(path):

    # Load wavefile
    signal, fs = librosa.load(path, sr=sample_rate)
    # mask, y_mean = envelope(signal, fs, threshold=threshold)
    # signal = signal[mask]
    # delta_sample = int(8000)

    # if signal.shape[0] < delta_sample:
    #     sample = np.zeros(shape=(delta_sample, ), dtype=np.int16)
    #     sample[: signal.shape[0]] = signal

    # else:
    #     trunc = signal.shape[0] % delta_sample
    #     for cnt, i in enumerate(np.arange(0, signal[0] - trunc)):
    #         start = int(i)
    #         stop = int(i + delta_sample)
    #         sample = signal[start:stop]

    # Create MFCCs from sound clip
    mfccs = python_speech_features.base.mfcc(signal,
                                             samplerate=fs,
                                             winlen=0.256,
                                             winstep=0.050,
                                             numcep=num_mfcc,
                                             nfilt=26,
                                             nfft=2048,
                                             preemph=0.97,
                                             ceplifter=0,
                                             appendEnergy=False,
                                             winfunc=np.hanning)
    return mfccs.transpose()

    # Function: Create MFCCs, keeping only ones of desired length


def extract_features(in_files, in_y):
    prob_cnt = 0
    out_x = []
    out_y = []

    for index, filename in enumerate(in_files):

        # Create path from given filename and target item
        path = join(dataset_path, target_list[int(in_y[index])],
                    filename)

        # Check to make sure we're reading a .wav file
        if not path.endswith('.wav'):
            continue

        # Create MFCCs
        mfccs = calc_mfcc(path)

        # Only keep MFCCs with given length
        if mfccs.shape[1] == len_mfcc:
            out_x.append(mfccs)
            out_y.append(in_y[index])
        else:
            print('Dropped:', index, mfccs.shape)
            prob_cnt += 1

    return out_x, out_y, prob_cnt


# Create train, validation, and test sets
x_train, y_train, prob = extract_features(filenames_train, y_orig_train)
print('Removed percentage:', prob / len(y_orig_train))
x_val, y_val, prob = extract_features(filenames_val, y_orig_val)
print('Removed percentage:', prob / len(y_orig_val))
x_test, y_test, prob = extract_features(filenames_test, y_orig_test)
print('Removed percentage:', prob / len(y_orig_test))


# Save features and truth vector (y) sets to disk
np.savez(feature_sets_file,
         x_train=x_train,
         y_train=y_train,
         x_val=x_val,
         y_val=y_val,
         x_test=x_test,
         y_test=y_test)