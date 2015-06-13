# -*- coding: utf-8 -*-
"""
Created on Sun May 17 10:58:17 2015

@author: aaronpayne
"""
# https://github.com/alexis-mignon/python-flickr-api/wiki/Tutorial
import flickr_api, argparse, yaml, os, datetime
from progressbar import ProgressBar, Counter, ETA
from helper import get_paths, dumpclean
from photo import photo
from photo_manager import photo_manager

debug = False

def main():
    yaml_config_dict = setup_arguments()
    initialize_flickr(yaml_config_dict)
    pmanager = photo_manager(yaml_config_dict)
    sync_local_photos(yaml_config_dict, pmanager)
    sync_flickr_photos(yaml_config_dict, pmanager)
    pmanager.close()
    print "Finished all syncing!"
    
def sync_flickr_photos(yaml_config_dict, pmanager):
    working_directory = yaml_config_dict["working_directory"]    
    user = flickr_api.test.login()
    photos = user.getPhotos()
    flickr_photo_count = photos.info.total
    tracked_photo_count = pmanager.get_photo_count()
    if flickr_photo_count > tracked_photo_count:
        print 'Flickr has photos that are not being tracked.  Downloading...'
        photos_to_download = list()
        for fphoto in photos:
            fid = fphoto.id
            if not pmanager.check_id(fid):
                photos_to_download.append(fphoto)
        photo_download_count = len(photos_to_download)
        pbar = ProgressBar(widgets=['Processed: ', Counter(), ' of '+str(photo_download_count)+' ', ETA()], maxval=photo_download_count).start()
        i = 0
        for fphoto in photos_to_download:
            i = i +1
            fid = fphoto.id
            temp_fphoto = photo(flickr_photo_obj=fphoto, working_directory=working_directory)
            pmanager.add_flickr_photo(temp_fphoto, yaml_config_dict["flickr_local"])
            pbar.update(i)
            print 'Downloaded: '+str(i)+'of '+str(photo_download_count)
        pbar.finish()
    
def sync_local_photos(yaml_config_dict, pmanager):
    print 'Syncing local photos...'
    supported_photo_types = yaml_config_dict['supported_photo_types']
    for photo_directory in yaml_config_dict['photo_directories']:
        print ' - Syncing directory: '+photo_directory
        process_directory(photo_directory, pmanager, supported_photo_types, yaml_config_dict["path_ignore"])
    if yaml_config_dict["upload_to_flickr"]:
        upload_local(pmanager, yaml_config_dict)
            
def upload_local(pmanager, yaml_config_dict):
    photos_to_upload = pmanager.get_photos_to_upload()
    i = 0
    if photos_to_upload != None:
        photo_upload_count = len(photos_to_upload)
        pbar = ProgressBar(widgets=['Processed: ', Counter(), ' of '+str(photo_upload_count)+' ', ETA()], maxval=photo_upload_count).start()
        for photo_upload in photos_to_upload:
            i = i +1
            photo_path = photo_upload[0]
            #print "Uploading: "+photo_path
            public = yaml_config_dict["photo_permissions"]["is_public"]
            family = yaml_config_dict["photo_permissions"]["is_family"]
            friend = yaml_config_dict["photo_permissions"]["is_friend"]
            #photo_id = i
            tags = pmanager.get_photo_tags(photo_upload[2])
            #print " ".join(tags)        
            flickr_photo = flickr_api.upload(photo_file = photo_path, 
                                         title = photo_upload[1],
                                         tags = " ".join(tags),
                                         is_public=public,
                                         is_friend=friend,
                                         is_family=family)
            upload_time = datetime.datetime.now()
            pmanager.add_upload_data(photo_path, photo_id=flickr_photo.id, public=public, family=family,
                                     friend=friend, upload_time=upload_time)
            if yaml_config_dict["archive"]:
                if debug:
                    print 'Archive on, so deleteing local copy: '+photo_path
                os.unlink(photo_path)
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
            i = i + 1
            sync_local_photo(file_path, pmanager, path_ignore)
    print "Syncing %i photos in local db" % i
    # I think get_paths is already walking the directory
    #for dir_path in directory_paths:
        #process_directory(dir_path, pmanager, file_types)
        
def sync_local_photo(photo_path, pmanager, path_ignore):
    """
    
    """
    local_photo = photo(local_photo=photo_path, path_ignore=path_ignore)
    pmanager.add_local_photo(local_photo)  
    
def setup_arguments():
    ap = argparse.ArgumentParser()
    print 'test'
    ap.add_argument("-y", "--yaml_config", 
                    required = False, 
                    help="YAML config file, default: flickr_sync.yaml", 
                    default="flickr_sync.yaml")
    ap.add_argument("-d", "--photo_directories", required=False, help="Overrides yaml photo directory", action="append")
    args = ap.parse_args()

    if os.path.exists(args.yaml_config):
        print 'yaml config exists! '+args.yaml_config
        yaml_handler = open(args.yaml_config, 'r')
        yaml_config = yaml.load(yaml_handler)
        yaml_handler.close()
    else:
        print 'YAML config file does not exist: '+args.yaml_config
        exit()
        
    if args.photo_directories != None:
        yaml_config['photo_directories'] = args.photo_directories
        
    if debug:
        print 'Dumping yaml_config'
        dumpclean(yaml_config)
    return yaml_config    

def initialize_flickr(yaml_config_dict):
    print 'Initializing flickr api information...'
    flickr_api.set_keys(api_key=yaml_config_dict['api_key'], api_secret=yaml_config_dict['api_secret'])
    flickr_api.set_auth_handler(yaml_config_dict['auth_token_path'])
    
if __name__ == "__main__":
    main()