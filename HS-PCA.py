# This program makes principal components analysis for hyperspectral images obtained 
# using MUSES9-HS hyperspectral camera.
# This program should be run from within a folder containing the 'Spectral_Cube' folder.

import os
import cv2
import numpy as np
import pandas as pd
from sklearn import decomposition
import warnings

file_list = os.listdir('Spectral_Cube/')
waves = []

for file in file_list:
    if 'image' in file:
        waves.append(int(file[5:file.find('.')]))

waves = sorted(waves)

scale = 0.5
roi_size = 1  # We take the size of the square for averaging
file_extension = 'jpg'  # We check the file extension of images
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

if not os.path.exists('Spectral_Cube/image1000.' + file_extension):
    file_extension = 'png'

df_spectrum = pd.DataFrame()
n = 0

for wave_length in waves:
    n += 1
    print(str(wave_length) + '-nm image uploaded', end='')
    single_wave_array = []
    image = cv2.imread('Spectral_Cube/image' + str(wave_length) + '.' + file_extension)
    height = image.shape[0]
    width = image.shape[1]
    dim = (int(width * scale), int(height * scale))
    small_image = cv2.resize(image, dim, interpolation=cv2.INTER_LINEAR)
    gray_image = cv2.cvtColor(small_image, cv2.COLOR_BGR2GRAY)
    single_wave_array = np.array(gray_image).flatten()
    df_spectrum[wave_length] = single_wave_array
    print('\r', end='')

# print(df_spectrum)
print('Principal component analysis is in progress. Please, wait.')
pca = decomposition.PCA()
spectral_pc = pca.fit_transform(df_spectrum)
spectral_pc_df = pd.DataFrame(data=spectral_pc, columns=['PC' + str(i) for i in range(n)])
# print(spectral_pc_df)

if not os.path.exists('PCA-Out'):
    os.mkdir('PCA-Out')

for pc in range(10):
    out_image = np.array(spectral_pc_df['PC' + str(pc)]).reshape([int(height * scale), int(width * scale)])
    out_image = 255 * (out_image - out_image.min()) / (out_image.max() - out_image.min())
    print('Image_PC' + str(pc + 1) + ' is in progress', end='')
    cv2.imwrite('PCA-Out/Image_PC' + str(pc + 1) + '.jpg', out_image)
    print('\r', end='')

# Load the grayscale images for red, green, and blue channels
print('Color images are in progress.')
for start in range(10 - 2):
    folder = 'PCA-Out/Image_PC'
    red_channel = cv2.imread(folder + str(start + 1) + '.jpg', 0)
    green_channel = cv2.imread(folder + str(start + 2) + '.jpg', 0)
    blue_channel = cv2.imread(folder + str(start + 3) + '.jpg', 0)

    # Create an empty RGB image
    rgb_image = np.zeros((red_channel.shape[0], red_channel.shape[1], 3), dtype=np.uint8)

    # Assign the grayscale images to the corresponding color channels of the RGB image
    rgb_image[:, :, 0] = blue_channel  # Blue channel
    rgb_image[:, :, 1] = green_channel  # Green channel
    rgb_image[:, :, 2] = red_channel  # Red channel

    # Display the RGB image
    cv2.imwrite('PCA-Out/RGB-ImagePC_' + str(start + 1) + '-' + str(start + 2) + '-' + str(start + 3) + '.jpg', rgb_image)

print('Finished!')
