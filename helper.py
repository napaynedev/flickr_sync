# -*- coding: utf-8 -*-
"""
Created on Wed May 20 20:01:36 2015

@author: root
"""

import hashlib, os

def get_paths(directory):
    """
    http://stackoverflow.com/questions/3207219/how-to-list-all-files-of-a-directory-in-python
    This function will generate the file names in a directory 
    tree by walking the tree either top-down or bottom-up. For each 
    directory in the tree rooted at directory top (including top itself), 
    it yields a 3-tuple (dirpath, dirnames, filenames).
    Edited to also return directory paths
    """
    file_paths = []  # List which will store all of the full filepaths.
    directory_paths = []

    # Walk the tree.
    for root, directories, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)  # Add it to the list.
        for directory in directories:
            directory_path = os.path.join(root, directory)  
            directory_paths.append(directory_path)

    return (file_paths, directory_paths)  # Self-explanatory.
    
def dumpclean(obj):
    """
    http://stackoverflow.com/questions/15785719/how-to-print-a-dictionary-line-by-line-in-python
    """
    if type(obj) == dict:
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                print k
                dumpclean(v)
            else:
                print '%s : %s' % (k, v)
    elif type(obj) == list:
        for v in obj:
            if hasattr(v, '__iter__'):
                dumpclean(v)
            else:
                print v
    else:
        print obj

def compute_image_hash(photo_path):
    """
    http://blog.iconfinder.com/detecting-duplicate-images-using-python/
    Previous method, issues with library:
    https://realpython.com/blog/python/fingerprinting-images-for-near-duplicate-detection/
    """
    image = open(photo_path).read()
    # http://stackoverflow.com/questions/3583265/compare-result-from-hexdigest-to-a-string
    h = hashlib.md5(image).hexdigest()
    return h
    
def is_special_directory_tag(text):
    result = False    
    if ':' in text:
        tag_parts = text.split(':')
        dir_index = tag_parts[0]
        if dir_index.isdigit():
            result = True
    return result