# -*- coding: utf-8 -*-
"""
Created on Sun May 17 10:58:17 2015

@author: aaronpayne
"""
# External Libraries
# https://github.com/alexis-mignon/python-flickr-api/wiki/Tutorial
import os
from progressbar import ProgressBar, Counter, ETA

# Project libraries
from helper import get_paths
from photo import photo
from photo_manager import photo_manager
from flickr_functions import flickr
from interface import setup_arguments

debug = False

def main():
    yaml_config_dict = setup_arguments()
    flickr_controller = flickr(yaml_config_dict)
    pmanager = photo_manager(yaml_config_dict)
    sync_local_photos(yaml_config_dict, pmanager, flickr_controller)
    sync_flickr_photos(yaml_config_dict, pmanager, flickr_controller)
    reset_tags(pmanager, yaml_config_dict, flickr_controller)
    pmanager.close()
    print "Finished all syncing!"
    
def reset_tags(pmanager, yaml_config_dict, flickr_controller):
    photos_needing_reset = pmanager.get_photos_tag_reset()
    if photos_needing_reset != None:
        count = len(photos_needing_reset)
        pbar = sync_pbar(count, title_prepend='Tag Resets')
        i = 0
        for single_photo in photos_needing_reset:
            i = i +1
            new_tags = single_photo.generate_tags(single_photo.containing_directory, path_ignore=yaml_config_dict['path_ignore'])
            single_photo.set_tags(new_tags)
            flickr_controller.reset_tags(single_photo.fid, new_tags)
            pmanager.reset_tags(single_photo.uid, new_tags)
            pbar.update(i)
        pbar.finish()
    
def sync_pbar(count, title_prepend=''):
    return ProgressBar(widgets=[title_prepend+' Processed: ', Counter(), ' of '+str(count)+' ', ETA()], maxval=count).start()
    
def sync_flickr_photos(yaml_config_dict, pmanager, flickr_controller):
    working_directory = yaml_config_dict["working_directory"]    
    photos = flickr_controller.get_photos()
    flickr_photo_count = flickr_controller.get_photo_count()
    tracked_photo_count = pmanager.get_photo_count()
    if flickr_photo_count > tracked_photo_count:
        print 'Flickr has photos that are not being tracked.  Downloading...'
        photos_to_download = list()
        for fphoto in photos:
            fid = fphoto.id
            if not pmanager.check_id(fid):
                photos_to_download.append(fphoto)
        photo_download_count = len(photos_to_download)
        pbar = sync_pbar(photo_download_count, title_prepend='Downloads')
        i = 0
        for fphoto in photos_to_download:
            i = i +1
            fid = fphoto.id
            temp_fphoto = photo(flickr_photo_obj=fphoto, working_directory=working_directory)
            pmanager.add_flickr_photo(temp_fphoto, yaml_config_dict["flickr_local"])
            pbar.update(i)
            # this print is to track a non-live download to file
            print 'Downloaded: '+str(i)+'of '+str(photo_download_count)
        pbar.finish()
    
def sync_local_photos(yaml_config_dict, pmanager, flickr_controller):
    print 'Syncing local photos...'
    supported_photo_types = yaml_config_dict['supported_photo_types']
    for photo_directory in yaml_config_dict['photo_directories']:
        print ' - Syncing directory: '+photo_directory
        process_directory(photo_directory, pmanager, supported_photo_types, yaml_config_dict["path_ignore"])
    if yaml_config_dict["upload_to_flickr"]:
        upload_local(pmanager, yaml_config_dict, flickr_controller)
            
def upload_local(pmanager, yaml_config_dict, flickr_controller):
    photos_to_upload = pmanager.get_photos_to_upload()
    i = 0
    if photos_to_upload != None:
        photo_upload_count = len(photos_to_upload)
        pbar = sync_pbar(photo_upload_count, title_prepend='Uploads')
        for photo_upload in photos_to_upload:
            i = i +1
            tags = pmanager.get_photo_tags(photo_upload.uid)
            upload_data = flickr_controller.upload_photo(photo_upload, tags, 
                                                         yaml_config_dict["photo_permissions"],
                                                         path_ignore=yaml_config_dict["path_ignore"])
            pmanager.add_upload_data(upload_data)
            if yaml_config_dict["archive"]:
                photo_path = photo_upload.photo_path                
                if debug:
                    print 'Archive on, so deleteing local copy: '+photo_path
                os.unlink(photo_path)
                #pmanager.archive()
            pbar.update(i)
            print 'Uploaded: '+str(i)+' of '+str(photo_upload_count)
        pbar.finish()
    print "Uploaded %i photos" % i
            
def process_directory(directory, pmanager, file_types, path_ignore):
    if debug:
        print 'process_directory: '+directory
    file_paths, directory_paths = get_paths(directory)
    i = 0    
    for file_path in file_paths:
        fname, extension = os.path.splitext(file_path)
        extension = extension.replace('.', '')
        if extension in file_types:
            if '.' not in fname:            
                i = i + 1
                sync_local_photo(file_path, pmanager, path_ignore)
            else:
                print file_path+' skipped due to . in name'
    print "Syncing %i photos in local db" % i
    # I think get_paths is already walking the directory
    #for dir_path in directory_paths:
        #process_directory(dir_path, pmanager, file_types)
        
def sync_local_photo(photo_path, pmanager, path_ignore):
    """
    
    """
    if debug:
        print 'Syncing local photo at: '+photo_path
        print 'Path ignore: '+str(path_ignore)
    local_photo = photo(local_photo=photo_path, path_ignore=path_ignore)
    pmanager.add_local_photo(local_photo)  
    
 
    
if __name__ == "__main__":
    main()