# -*- coding: utf-8 -*-
"""
Created on Sat Jun 13 09:21:50 2015

@author: root
"""
import flickr_api, datetime, photo

class flickr(object):
    def __init__(self, setup_dict):
        self.initialize_flickr(setup_dict)
        self.user = self._flickr_get_user()
        self.photos = self._flickr_get_photos()
        self.stale = False
    
    def initialize_flickr(self, yaml_config_dict):
        print 'Initializing flickr api information...'
        flickr_api.set_keys(api_key=yaml_config_dict['api_key'], api_secret=yaml_config_dict['api_secret'])
        flickr_api.set_auth_handler(yaml_config_dict['auth_token_path'])
        
    def _flickr_get_user(self):
        return flickr_api.test.login()
        
    def get_user(self):
        return self.user
        
    def _flickr_get_photos(self):
        user = self.get_user()
        return user.getPhotos()
        
    def get_photos(self):
        return self.photos
        
    def get_photo_count(self):
        return self.photos.info.total
        
    def print_photos(self, photo_list):
        for single_photo in photo_list:
            photo_obj = photo(single_photo)
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
        
    def remove_all_path_tags(self, photo_id, tag_list=None):
        if self.stale:
            self._flickr_get_photos()
        for single_photo in self.photos:
            if photo_id == single_photo.id:
                for tag in single_photo.tags:
                    if tag_list == None:
                        tag.remove()
                    else:
                        if tag.raw in tag_list:
                            tag.remove()
    
    def remove_tag(self, photo_id, tag_label):
        self.remove_all_path_tags(photo_id, tag_list=[tag_label])