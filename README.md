# Nonwoven Material Image Embossing Pattern Quality Assessment

Nonwoven embossing qualitiy assessment tool by image processing. Quality results is a number in [0, 1] for one image, higher is better. 

The template is like below. <br>
![Pattern](https://github.com/lifengzhao/nonwoven_image_pattern_quality/blob/main/template_thicken4.png 'pattern')

Currently only .jpg and .cr2 files are supported.


Usage:
Run code only, images in all subdirs of current folder will be assessed, and a "results.csv" file will be saved.<br>
   `$ python OCNW_pattern_quality.py`
Or, run the code with one image file name as input, will print out the assessment result, no file saved. <br>
   `$ python OCNW_pattern_quality.py image_file_name.jpg`
