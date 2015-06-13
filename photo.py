# -*- coding: utf-8 -*-
"""
Created on Wed May 20 20:03:55 2015

@author: root
"""

import os
from helper import compute_image_hash

debug = True

class photo(object):
    def __init__(self, local_photo=None, flickr_photo=None):
        if local_photo != None:
            self.process_local_photo(local_photo)
        elif flickr_photo != None:
            pass
        else:
            print 'Photo class requires some sort of photo input'
            exit()
            
    def process_local_photo(self, photo_path):
        self.photo_path = photo_path        
        self.containing_directory, self.filename = os.path.split(photo_path)
        self.fname, self.extension = os.path.splitext(self.filename)
        self.extension = self.extension.replace('.', '')
        photo_stats = os.stat(self.photo_path)
        self.size = photo_stats.st_size
        self.modified_time = photo_stats.st_mtime
        self.containing_directory.replace('\\', '/')
        self.tags = self._filter_tags(self.containing_directory.split('/'))
        self.hash = compute_image_hash(self.photo_path)
        if debug:
            print 'path:'+self.photo_path+\
                  ' containing directory: '+self.containing_directory+\
                  ' filename: '+self.filename+\
                  ' fname: '+self.fname+\
                  ' extension: '+self.extension+\
                  ' size: '+str(self.size)+\
                  ' modified time: '+str(self.modified_time)
            for tag in self.tags:
                print 'tag: '+tag
            
    def _filter_tags(self, tag_list):
        new_tag_list = []    
        i = 0
        for tag in tag_list:
            if tag != '':
                new_tag_list.append(str(i)+':'+tag)
                i += 1
        return new_tag_list