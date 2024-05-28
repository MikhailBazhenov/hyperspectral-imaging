# This program performs flat field correction, dark current correction,
# and correction for the 'Spectralon' standard having equal reflectances at any wavelength.
#
# First, create a file named 'folder_list.txt'
# In this file place the names of folders containing the following data:
# the first three folders must contain Spectralon, Dark_frame and White_frame images correspondingly.
# Other folders should contain the images of research objects.
# Example 'folder_list.txt':
# 23.01.2024_Spectralon
# 23.01.2024_Dark_current
# 23.01.2024_Flat_field
# 23.01.2024_Ficus
# 23.01.2024_Banana

import cv2
import os


def select_rectangle(event, x, y, flags, param):
    global top_left_pt, bottom_right_pt, selecting

    if event == cv2.EVENT_LBUTTONDOWN:
        top_left_pt = (x, y)
        selecting = True

    elif event == cv2.EVENT_LBUTTONUP:
        bottom_right_pt = (x, y)
        selecting = False
        cv2.rectangle(resized_image_1000, top_left_pt, bottom_right_pt, (0, 255, 0), 2)
        cv2.imshow("Spectralon", resized_image_1000)


# Reading the folder list from file.
f1 = open('folder_list.txt', 'r')
folder_list = []
for line in f1:
    line = line.strip()
    if line != '':
        folder_list.append(line)
folder_number = 0

# Initialize variables
brightness = 0.8
scale = 1
selecting = False
top_left_pt = None
bottom_right_pt = None
finished = False
spectralon_spectrum = []
file_extension = '.jpg'  # preliminary we take file extension .jpg

# the dimensions for image that will be shown on screen
max_width = 800
max_height = 600

for folder in folder_list:
    folder_number += 1
    # Here we indicate the folders we are working with
    if folder_number == 1:
        spectralon_folder = folder + '/Spectral_Cube/'  # The images of Spectralon standard
        continue
    if folder_number == 2:
        dark_image_folder = folder + '/Spectral_Cube/'  # Dark field images
        continue
    if folder_number == 3:
        white_image_folder = folder + '/Spectral_Cube/'  # White field images
        continue
    if folder_number > 3:
        object_image_folder = folder + '/Spectral_Cube/'  # The images of we are correcting
        output_folder = 'Corrected_' + folder + '/Spectral_Cube/'  # The corrected images

    # If output folder not exist, we create it
    if not os.path.exists(output_folder.split('/')[0]):
        os.mkdir(output_folder.split('/')[0])
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)

    if folder_number == 4:
        # Load the spectralon image at 1000 nm
        if not os.path.exists(spectralon_folder + 'image1000' + file_extension):
            file_extension = '.png'  # correct file extension if needed
        spectralon_image_1000 = cv2.imread(spectralon_folder + 'image1000' + file_extension)
        print('Image file extension is ' + file_extension)

        # Resize the image to display it
        if spectralon_image_1000.shape[1] > max_width or spectralon_image_1000.shape[0] > max_height:
            scale = min(max_width / spectralon_image_1000.shape[1], max_height / spectralon_image_1000.shape[0])
            resized_image_1000 = cv2.resize(spectralon_image_1000, None, fx=scale, fy=scale)
        else:
            resized_image_1000 = spectralon_image_1000

        # Create a window and set mouse callback function
        cv2.namedWindow("Spectralon")
        cv2.setMouseCallback("Spectralon", select_rectangle)
        print('Select a part of spectralon. Press <r> to reselect or <p> to proceed')

        # Selecting part of spectralon to get its standard spectrum
        while True:
            cv2.imshow("Spectralon", resized_image_1000)
            key = cv2.waitKey(1) & 0xFF

            # Press 'r' to reset the selection
            if key == ord("r"):
                spectralon_image_1000 = cv2.imread(spectralon_folder + 'image1000' + file_extension)
                print('Select a part of spectralon. Press <'r'> to reselect or <p> to proceed')
                if spectralon_image_1000.shape[1] > max_width or spectralon_image_1000.shape[0] > max_height:
                    scale = min(max_width / spectralon_image_1000.shape[1], max_height / spectralon_image_1000.shape[0])
                    resized_image_1000 = cv2.resize(spectralon_image_1000, None, fx=scale, fy=scale)
                top_left_pt = None
                bottom_right_pt = None

            # Press 'p' to proceed
            elif key == ord("p"):
                print('Spectralon spectrum is in progress\nNow you can control the content of ROI frame')
                break

            # Display the selected coordinates
            if selecting and top_left_pt is not None:
                cv2.putText(resized_image_1000, f"Top Left: {int(top_left_pt[0] / scale), int(top_left_pt[1] / scale)}",
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                finished = False
            if not selecting and top_left_pt is not None and bottom_right_pt is not None and not finished:
                cv2.putText(resized_image_1000,
                            f"Bottom Right: {int(bottom_right_pt[0] / scale), int(bottom_right_pt[1] / scale)}",
                            (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Taking the spectrum of spectralon
        for wave_length in [365] + list(range(400, 1001, 5)):
            spectralon_image = cv2.imread(spectralon_folder + 'image' + str(wave_length) + file_extension)
            white_image = cv2.imread(white_image_folder + 'image' + str(wave_length) + file_extension)
            dark_image = cv2.imread(dark_image_folder + 'image' + str(wave_length) + file_extension)
            corrected_image = (spectralon_image - dark_image) / white_image  # We make white field correction for spectralon
            roi = corrected_image[int(top_left_pt[1] / scale):int(bottom_right_pt[1] / scale),
                  int(top_left_pt[0] / scale):int(bottom_right_pt[0] / scale)]
            cv2.imshow("ROI", roi / 2)
            key = cv2.waitKey(1) & 0xFF
            mean_value = roi.mean()
            spectralon_spectrum.append([wave_length, mean_value])

        spectrum = {}  # This is spectralon spectrum
        for wave_length in spectralon_spectrum:
            spectrum[wave_length[0]] = wave_length[1]
        cv2.destroyAllWindows()


    # Making correction
    print('Correction of ' + folder + ' images is in progress')
    for wave_length in [365] + list(range(400, 1001, 5)):
        white_image = cv2.imread(white_image_folder + 'image' + str(wave_length) + file_extension)
        object_image = cv2.imread(object_image_folder + 'image' + str(wave_length) + file_extension)
        dark_image = cv2.imread(dark_image_folder + 'image' + str(wave_length) + file_extension)

        # Making correction
        corrected_image = brightness * cv2.subtract(object_image, dark_image) / (white_image * spectrum[wave_length])

        if corrected_image.shape[1] > max_width or corrected_image.shape[0] > max_height:
            scale = min(max_width / corrected_image.shape[1], max_height / corrected_image.shape[0])
            reduced_image = cv2.resize(corrected_image, None, fx=scale, fy=scale)
        else:
            reduced_image = corrected_image

        cv2.namedWindow("Image")
        cv2.putText(reduced_image, f"Wave length : {wave_length} nm", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Image", reduced_image)
        cv2.waitKey(1)
        corrected_image = cv2.convertScaleAbs(corrected_image, alpha=255)
        cv2.imwrite(output_folder + 'image' + str(wave_length) + file_extension, corrected_image)

    cv2.destroyAllWindows()
print('Ready')