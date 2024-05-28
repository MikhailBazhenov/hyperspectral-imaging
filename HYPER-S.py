# This program calculates the average spectrum of the selected rectangle areas
# in images taken by the MUSES9-HS hyperspectral camera.
# The folder_list.txt file is the same that is used by image_correction.py, and should contain at least 4 lines:
# Spectralon -- is not used by this program (could be empty line)
# Dark_current -- is not used by this program (could be empty line)
# Flat_field -- is not used by this program (could be empty line)
# Object_folder -- the images of the object of interest. The 'Spectral_Cube' folder should be within this folder.

import cv2
import numpy as np
import pandas as pd
import os


def select_rectangle(event, x, y, flags, param):
    global top_left_pt, bottom_right_pt, selecting

    if event == cv2.EVENT_LBUTTONDOWN:
        top_left_pt = [x, y]
        selecting = True

    elif event == cv2.EVENT_LBUTTONUP:
        bottom_right_pt = [x, y]
        selecting = False
        # Replacing coordinates values if not in right order
        if top_left_pt[0] > bottom_right_pt[0]:
            temp_var = bottom_right_pt[0]
            bottom_right_pt[0] = top_left_pt[0]
            top_left_pt[0] = temp_var
        if top_left_pt[1] > bottom_right_pt[1]:
            temp_var = bottom_right_pt[1]
            bottom_right_pt[1] = top_left_pt[1]
            top_left_pt[1] = temp_var
        cv2.rectangle(image_1000, top_left_pt, bottom_right_pt, (0, 255, 0), 1)
        cv2.imshow("Image", image_1000)


print('This program takes the spectrum of the region of interest (ROI) from hyperspectral camera images.')
folder_prefix_corrected = input('Do you want to process folders with prefix <Corrected_> ? (y/n):')
yes = ['y', 'Y']
# making folder for ROI screenshots
if not os.path.exists('ROI'):
    os.mkdir('ROI')

# Reading the folder list from file.
f1 = open('folder_list.txt', 'r')
folder_list = []
for line in f1:
    line = line.strip()
    if line != '':
        folder_list.append(line)
folder_number = 0

# window size to display images
max_width = 800
max_height = 600

# waves = [365] + list(range(400, 1001, 5))

file_list = os.listdir(folder_list[3] + '/Spectral_Cube')
waves = []

for file in file_list:
    if 'image' in file:
        waves.append(file[5:file.find('.')])

waves = sorted(waves, key=int)
spectral_bands = []

for wave_length in waves:
    spectral_bands.append(int(wave_length))

print('The band list:')
print(waves)

df_mean = pd.DataFrame()
df_sd = pd.DataFrame()
df_mean.index = spectral_bands
df_sd.index = spectral_bands
df_mean.index.name = 'Wavelength'
df_sd.index.name = 'Wavelength'

for folder_name in folder_list:
    folder_number += 1
    if folder_number < 4:
        continue
    if folder_prefix_corrected in yes:
        folder_name = 'Corrected_' + folder_name
    if not os.path.exists(folder_name):
        print('A folder <' + folder_name + '> not found!')
        continue
    # Load the image for area selection
    band = len(spectral_bands) - 1
    image_file = folder_name + '/Spectral_Cube/image' + str(spectral_bands[band])
    file_extension = 'jpg'
    if not os.path.exists(image_file + '.' + file_extension):
        file_extension = 'png'

    image_1000 = cv2.imread(image_file + '.' + file_extension)
    print('The file extension of images is ' + file_extension + '.')

    # Resize the image_1000 to fit the screen
    if image_1000.shape[1] > max_width or image_1000.shape[0] > max_height:
        scale = min(max_width / image_1000.shape[1], max_height / image_1000.shape[0])
        image_1000 = cv2.resize(image_1000, None, fx=scale, fy=scale)

    # Create a window and set mouse callback function
    cv2.namedWindow("Image")
    cv2.setMouseCallback("Image", select_rectangle)
    print('Now ' + waves[band] + ' nm image from folder <' + folder_name + '> is displayed')
    print('Please, make the image window active.')
    print('Use <w> and <s> keys to select an image on different wavelength.')
    print('To move to the next folder, press <n>, or <q> to quit.')
    print('First, using mouse select a part of black background.')
    print('Press <x> if there is no black background or you do not wish to remove it.')
    # The idea is that the intensities of pixels within ROI will be summarized,
    # only if these pixels are statistically different from black background (mean_background + 7*SD).
    # Seven standard deviations is an empirically optimal value, but if you wish to change it,
    # you can do it below:

    sd_number = 7

    # Initialize variables
    selecting = False
    top_left_pt = None
    bottom_right_pt = None
    finished = False
    j = 0
    background_spectrum = []
    background_measured = False
    base = 0

    while True:
        cv2.imshow("Image", image_1000)
        key = cv2.waitKey(1) & 0xFF
        cv2.putText(image_1000, str(spectral_bands[band]), (max_width - 70, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 1)

        # Press 'r' to reset the selection
        if key == ord("r") or finished:
            image_1000 = cv2.imread(image_file + '.' + file_extension)
            if image_1000.shape[1] > max_width or image_1000.shape[0] > max_height:
                scale = min(max_width / image_1000.shape[1], max_height / image_1000.shape[0])
                image_1000 = cv2.resize(image_1000, None, fx=scale, fy=scale)
            top_left_pt = None
            bottom_right_pt = None
            finished = False

        elif key == ord('s'):
            if band != 0:
                band = band - 1
            image_file = folder_name + '/Spectral_Cube/image' + str(spectral_bands[band])
            image_1000 = cv2.imread(image_file + '.' + file_extension)
            if image_1000.shape[1] > max_width or image_1000.shape[0] > max_height:
                scale = min(max_width / image_1000.shape[1], max_height / image_1000.shape[0])
                image_1000 = cv2.resize(image_1000, None, fx=scale, fy=scale)
            top_left_pt = None
            bottom_right_pt = None

        elif key == ord('w'):
            if band != len(spectral_bands) - 1:
                band = band + 1
            image_file = folder_name + '/Spectral_Cube/image' + str(spectral_bands[band])
            image_1000 = cv2.imread(image_file + '.' + file_extension)
            if image_1000.shape[1] > max_width or image_1000.shape[0] > max_height:
                scale = min(max_width / image_1000.shape[1], max_height / image_1000.shape[0])
                image_1000 = cv2.resize(image_1000, None, fx=scale, fy=scale)
            top_left_pt = None
            bottom_right_pt = None

        elif key == ord('x'):
            for wave_length in waves:
                background_spectrum.append([wave_length, 0, 0])
            background_measured = True
            print('No background will be subtracted.')
            print('Use a mouse to select ROI, or press <n> to move to the next folder, or <q> to quit.')

        # Press 'q' to quit the program
        elif key == ord('q'):
            exit()

        elif key == ord('n'):
            break

        # Display the selected coordinates
        if selecting and top_left_pt is not None:
            finished = False
        if not selecting and top_left_pt is not None and bottom_right_pt is not None and not finished:
            spectrum = []
            print('Wait.')
            # Counting the number of lit pixels on 1000 nm shot.
            # We do it because on 1000 nm image the reflectance values are usually high enough,
            # especially in comparison to UV range reflectances.
            # Thus, we take the number of lit pixels in 1000 nm image as a base number of pixels.
            # In next steps we will summarize intensities of pixels over entire ROI and divide by the basal
            # number of pixels. This is made because the image of an object can move a bit from
            # one wavelength to another.
            if background_measured:
                image_file = folder_name + '/Spectral_Cube/image' + str(spectral_bands[band])
                image = cv2.imread(image_file + '.' + file_extension)
                roi = image[int(top_left_pt[1] / scale):int(bottom_right_pt[1] / scale),
                      int(top_left_pt[0] / scale):int(bottom_right_pt[0] / scale)]
                value_array = np.array(roi)
                min_value = 0
                for i in background_spectrum:
                    if i[0] == 1000:
                        min_value = i[1] + sd_number * i[2]
                if len(value_array[value_array > min_value]) > 0:
                    base = np.count_nonzero(value_array[value_array > min_value])
                    print('Basal number of pixels = ' + str(base))
                    print('Wait.')

            for wave_length in waves:
                image = cv2.imread(folder_name + '/Spectral_Cube/image' + str(wave_length) + '.' + file_extension)
                roi = image[int(top_left_pt[1] / scale):int(bottom_right_pt[1] / scale),
                      int(top_left_pt[0] / scale):int(bottom_right_pt[0] / scale)]
                value_array = np.array(roi)
                min_value = 0
                if background_measured:
                    for i in background_spectrum:
                        if i[0] == wave_length:
                            min_value = i[1] + sd_number * i[2]
                if len(value_array[value_array > min_value]) > 0 and base > 0:
                    mean_value = value_array[value_array > min_value].sum() / base
                    base2 = np.count_nonzero(value_array[value_array > min_value])
                    sd_value = (value_array[value_array > min_value].std() ** 2 * base2 / base) ** 0.5
                elif len(value_array[value_array > min_value]) > 0 and base == 0:
                    mean_value = value_array[value_array > min_value].mean()
                    sd_value = value_array[value_array > min_value].std()
                else:
                    mean_value = 0
                    sd_value = 0
                if background_measured:
                    spectrum.append([wave_length, mean_value, sd_value])
                else:
                    background_spectrum.append([wave_length, mean_value, sd_value])

            background_measured_past = background_measured

            if len(background_spectrum) > 1:
                background_measured = True

            if background_measured != background_measured_past:
                print('Background was measured. Now the pixels lower than (mean_background + 7*SD)')
                print('will not be accounted for in ROI that will be selected further.')
                print('To change the number before SD in the formula, edit the program line 120.')
                print('')
                print('Please, select ROI or press <n> to move to the next folder, or <q> to quit without saving.')
                cv2.imwrite('ROI/' + folder_name + '_Background.' + file_extension, image_1000)
                means = []
                sds = []
                for out in background_spectrum:
                    means.append(out[1])
                    sds.append(out[2])
                df_mean[folder_name + '|Background'] = means
                df_sd[folder_name + '|Background'] = sds

            if len(spectrum) > 0:
                print('Select another ROI or press <n> to move to the next folder, or <q> to quit without saving.')
                cv2.imwrite('ROI/' + folder_name + '_Measurement_' + str(j) + '.' + file_extension, image_1000)
                j += 1
                means = []
                sds = []
                for out in spectrum:
                    means.append(out[1])
                    sds.append(out[2])
                df_mean[folder_name + '|Measurement_' + str(j)] = means
                df_sd[folder_name + '|Measurement_' + str(j)] = sds
            finished = True

    cv2.destroyAllWindows()

with pd.ExcelWriter('spectrum.xlsx', engine='xlsxwriter') as writer:
    df_mean.to_excel(writer, sheet_name='Means', index=True)
    df_sd.to_excel(writer, sheet_name='SD', index=True)