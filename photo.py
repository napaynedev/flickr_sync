# -*- coding: utf-8 -*-
"""
Created on Wed May 20 20:03:55 2015

@author: root
"""

import os, shutil, datetime
from helper import compute_image_hash, is_special_directory_tag

debug = False

class photo(object):
    def __init__(self, local_photo=None, path_ignore=None, 
                 flickr_photo_obj=None, working_directory=None, download=True,
                 db_entry=None):
        if debug:
            print 'Attempting to create a photo'
        self.photo_path = None        
        self.containing_directory = None
        self.filename = None
        self.fname = None
        self.extension = None
        self.size = None
        self.modified_time = None
        self.tags = None
        self.hash = None
        assert local_photo != None or flickr_photo_obj != None and working_directory!= None or db_entry != None
        if local_photo != None:
            self._process_local_photo(local_photo, path_ignore)
        elif flickr_photo_obj != None and working_directory != None:
            self._process_flickr_photo(flickr_photo_obj, working_directory, download)
        elif db_entry != None:
            self._process_db_photo(db_entry)
        else:
            print 'Photo class requires some sort of photo input'
            exit()
        if debug:
            print self
            
    def _process_flickr_photo(self, flickr_obj, working_directory, download):
        #print 'Processing a flickr photo'        
        self.filename = flickr_obj.title
        if '.' not in self.filename:
            self.filename = self.filename+'.JPG'
        self.fid = flickr_obj.id
        self.fname, self.extension = self._get_fname_and_extension(self.filename)
        if download:
            self.photo_path = working_directory+'/'+self.filename
            flickr_obj.save(self.photo_path)
            self.download_time = datetime.datetime.now()
            self._compute_hash()
            self._get_size_and_mtime()
        self._process_flickr_tags(flickr_obj)
        self.ispublic = flickr_obj.ispublic
        self.isfamily = flickr_obj.isfamily
        self.isfriend = flickr_obj.isfriend
        
    def move_flickr_to_local(self, photo_dir):
        new_path = self._construct_local_path(photo_dir)+'/'+self.filename
        if not os.path.exists(new_path):
            self.containing_directory = self._get_containing_and_filename(new_path)[0]
            if not os.path.exists(self.containing_directory):
                os.makedirs(self.containing_directory)
            shutil.copy2(self.photo_path, new_path)
            os.unlink(self.photo_path)
            self.photo_path = new_path
            return True
        else:
            print 'A local photo already exists at this location: '+new_path
            return False
        
    def _construct_local_path(self, photo_dir):
        path_dir_dict = dict()
        last_index = 0
        for tag in self.tags:
            if is_special_directory_tag(tag):
                tag_parts = tag.split(':')
                dir_index = tag_parts[0]                
                dir_index = int(dir_index)
                path_dir_dict[dir_index] = tag_parts[1]
                if dir_index > last_index:
                    last_index = dir_index
        path_list = list()
        if 0 in path_dir_dict:
            for i in range(0,last_index):
                path_list.append(path_dir_dict[i])
        return photo_dir+'/'+'/'.join(path_list)        
        
    def _process_flickr_tags(self, flickr_obj):
        self.tags = []        
        for tag in flickr_obj.tags:
            self.tags.append(tag.raw)      
            
    def set_tags(self, new_tags):
        self.tags = new_tags
            
    def _process_db_photo(self, db_entry):
        """
        This function should not receive uid and fid
        """
        self.photo_path = db_entry[0]
        self.containing_directory, self.filename = self._get_containing_and_filename(self.photo_path)
        self.fname= self._get_fname_and_extension(self.filename)[0]
        self.extension = db_entry[1]
        self.size = db_entry[2]
        self.modified_time = db_entry[3]
        self.hash = db_entry[4]
        
    def _get_containing_and_filename(self, path):
        if debug:
            print 'Getting containing directory and filename for: '+path
        containing, filename = os.path.split(path)
        containing.replace('\\', '/')
        return (containing, filename)
        
    def _get_fname_and_extension(self, filename):
        fname, extension = os.path.splitext(filename)
        extension = extension.replace('.', '')
        return (fname, extension)
            
    def _process_local_photo(self, photo_path, path_ignore):
        """
        http://stackoverflow.com/questions/2104080/how-to-check-file-size-in-python
        """
        if debug:
            print 'Processing local photo at: '+photo_path
            print 'Ignoring the portion of the path: '+str(path_ignore)
        self.photo_path = photo_path        
        self.containing_directory, self.filename = self._get_containing_and_filename(photo_path)
        self.fname, self.extension = self._get_fname_and_extension(self.filename)        
        self._get_size_and_mtime()        
        self.tags = self.generate_tags(self.containing_directory, path_ignore)
        self._compute_hash()
        
    def _get_size_and_mtime(self):
        photo_stats = os.stat(self.photo_path)
        self.size = photo_stats.st_size
        #print "Photo size:"+str(self.size)
        self.modified_time = photo_stats.st_mtime
        
    def _compute_hash(self):
        self.hash = compute_image_hash(self.photo_path)

    def generate_tags(self, tag_string, path_ignore=None):
        if path_ignore != None:
            tag_string = tag_string.replace(path_ignore, '')
        if debug:
            print 'Creating tags out of: '+tag_string
        return self._filter_tags(tag_string.split('/'))
            
    def _filter_tags(self, tag_list):
        new_tag_list = []    
        i = 0
        for tag in tag_list:
            if tag != '':
                new_tag_list.append(str(i)+':'+tag)
                i += 1
        return new_tag_list
        
    def __str__(self):
        """
        http://stackoverflow.com/questions/1535327/python-how-to-print-a-class-or-objects-of-class-using-print
        """
        string = "Photo with the following attributes:"+\
                 " photo_path: "+str(self.photo_path)+\
                 " containing directory: "+str(self.containing_directory)+\
                 " filename: "+str(self.filename)+\
                 " fname: "+str(self.fname)+\
                 " extension: "+str(self.extension)+\
                 " size: "+str(self.size)+\
                 " modified time: "+str(self.modified_time)+\
                 " hash: "+str(self.hash)+\
                 " tags: "
        if self.tags != None:
            for tag in self.tags:
                string = string + str(tag)+" "
        return string

class db_photo(photo):
    """
    http://learnpythonthehardway.org/book/ex44.html
    """
    def __init__(self, uid = None, fid= None, db_entry=None, **kwargs):        
        if db_entry != None:
            self._process_db_entry(db_entry)
        else:
            super(db_photo, self).__init__(**kwargs)        
            self.uid = uid
            self.fid = fid
            
    def _process_db_entry(self, entry):
        """
        http://www.dotnetperls.com/slice
        """
        self.uid = entry[0]
        self.fid = entry[1]
        super(db_photo, self).__init__(db_entry=entry[2:])
        
    def __str__(self):
        string = super(db_photo, self).__str__()
        string = string + " uid: "+str(self.uid)+" fid: "+str(self.fid)
        return string           