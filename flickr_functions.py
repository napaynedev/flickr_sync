# -*- coding: utf-8 -*-
"""
Created on Sat Jun 13 09:21:50 2015

@author: root
"""
import flickr_api, datetime, photo
from helper import is_special_directory_tag

debug = True

class flickr(object):
    def __init__(self, setup_dict):
        self.stale = True
        self._initialize_flickr(setup_dict)
        self.user = self._flickr_get_user()
        self.photos = None
        self._flickr_get_photos()
        self.working_directory = setup_dict['working_directory']        
    
    def _initialize_flickr(self, yaml_config_dict):
        print 'Initializing flickr api information...'
        flickr_api.set_keys(api_key=yaml_config_dict['api_key'], api_secret=yaml_config_dict['api_secret'])
        flickr_api.set_auth_handler(yaml_config_dict['auth_token_path'])
        
    def _flickr_get_user(self):
        return flickr_api.test.login()
        
    def get_user(self):
        return self.user
        
    def _flickr_get_photos(self):
        user = self.get_user()
        self.photos = user.getPhotos()
        self.stale = False        
        
    def get_photos(self):
        return self.photos
        
    def get_photo_count(self):
        if self.stale:
            self._flickr_get_photos()
        return self.photos.info.total
        
    def print_photos(self, photo_id_list):
        if self.stale:
            self._flickr_get_photos()
        printed_photos = dict()
        for single_photo in self.photos:
            if single_photo.id in photo_id_list and single_photo.id not in printed_photos:
                printed_photos[single_photo.id] = True
                photo_obj = photo.photo(flickr_photo_obj=single_photo, working_directory=self.working_directory, download=False)
                print photo_obj
        
    def upload_photo(self, photo, tags, permissions):
        flickr_info_dict = dict()
        flickr_info_dict['path'] = photo.photo_path        
        flickr_info_dict['public'] = permissions['is_public']
        flickr_info_dict['family'] = permissions['is_family']
        flickr_info_dict['friend'] = permissions['is_friend']
        flickr_info_dict['upload_time'] = datetime.datetime.now()
        flickr_photo = flickr_api.upload(photo_file = flickr_info_dict['path'], 
                                         title = photo.filename,
                                         tags = " ".join(tags),
                                         is_public=flickr_info_dict['public'],
                                         is_friend=flickr_info_dict['friend'],
                                         is_family=flickr_info_dict['family'])
        flickr_info_dict['fid'] = flickr_photo.id
        self.stale = True
        return flickr_info_dict
        
    def remove_all_tags(self, photo_id, tag_list=None, filter_directory_tags=True):
        if self.stale:
            self._flickr_get_photos()
        for single_photo in self.photos:
            if debug:
                print "single photo is: "+str(single_photo.id)
                print 'input photo is %d' % (photo_id)
            if photo_id == int(single_photo.id):
                if debug:
                    print 'Found photo to remove tags from!'
                for tag in single_photo.tags:
                    tag_text = tag.raw                    
                    remove = False
                    if tag_list == None:
                        remove = True
                    else:
                        if tag_text in tag_list:
                            remove = True
                    # If we aren't filtering, don't remove non-special tags
                    if filter_directory_tags:
                        if not is_special_directory_tag(tag_text):
                            remove = False
                    if remove:
                        if debug:
                            print 'Removing tag: '+tag.raw
                        tag.remove()
                        self.stale = True
    
    def remove_tag(self, photo_id, tag_label):
        self.remove_all_tags(photo_id, tag_list=[tag_label])
        
    def add_tags(self, photo_id, tag_list):
        if self.stale:
            self._flickr_get_photos()
        for single_photo in self.photos:
            if photo_id == int(single_photo.id):
                if debug:
                    print 'Found photo and adding requested tags'
                single_photo.addTags(tag_list)
                self.stale = True
                
    def reset_tags(self, photo_id, tag_list):
        if debug:
            print 'Resetting tags on: '+str(photo_id)
        self.remove_all_tags(photo_id)
        self.add_tags(photo_id, tag_list)