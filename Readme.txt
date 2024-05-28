This set of programs has been designed to process images taken by the MUSES 9HS hyperspectral camera. The instructions below will guide you through the process.

IMAGE CORRECTION

We have noticed that images captured with the MUSES 9HS using its original light source require flat-field correction to accurately measure the reflectance of objects in their spectral cubes. The "image_correction.py" program provides the tools for performing this correction, as well as dark current correction and calibration against a reference small target (spectralon disc).
To perform the correction, you should follow these steps:
1)	Place the camera in a position where it can shoot the object, and place a flat screen (any even white or gray surface) at a height and distance that the object will be in front of.
2)	Adjust the light sources and calibrate the camera against a small target using a spectralon (place the spectralon at the brightest part of the screen).
3)	Take a spectral cube of a small spectralon target in front of the screen.
4)	Remove the small spectralon target and take a spectral cube of an even screen (which will be the flat field).
5)	Replace the bright screen with a dark (black) screen. Leave the camera and light sources unchanged. Place an object of interest in front of the dark screen and take its spectral cube.
6)	Cover the lens of the camera with a light-blocking material and take a spectral cube of the current dark image.
7)	Place all the recorded folders (obtained by the MUSES9-HS software) in one common folder, fill the "folder_list.txt" file as indicated in the example file and place it in the common folder. The number of object folders can be as many as necessary.
8)	Copy the image_correction.py file to the common folder and run it, following the instructions on the screen. Corrected images will be placed in folders with a 'Corrected_' prefix.

TAKING AVARAGE SPECTRA FROM SPECTRAL CUBES

After correction, you can immediately run the "HYPER-S.py" program and follow the instructions on the screen. This program calculates the average spectra of selected rectangle areas from spectral cube images taken by the MUSES9-HS hyperspectral camera and saves them in an Excel file.
It uses the "folder_list.txt" file, which should contain at least four lines:
Line 1: "Spectralon" - a folder containing a spectral cube of Spectralon (this line can be empty).
Line 2: "Dark_current" - a folder containing a dark current spectral cube (this line can also be empty).
Line 3: "Flat_field" - a folder with a spectral cube from a flat field (this line is optional).
Line 4: "Object_folder" - the folder containing uncorrected images of the object you want to analyze. The program will ask whether you want to use a folder with "Corrected_" prefix.

SPECTAL CURVES SMOOTHING

After generating the "spectrum.xlsx" file in the previous step, please run the program "Savitzky-Golay.py" immediately to perform smoothing on the spectrum data using the Savitzky-Golay filter. The output will be placed on a separate sheet within the "spectrum.xlsx" file.

PCA ANALYSIS OF THE SPECTRAL CUBE

To perform principal component analyses on the spectra within the spectral cube, please run the program "HS-PCA.py" from the directory where the "Spectral_Cube" folder is located.
