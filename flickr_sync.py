# -*- coding: utf-8 -*-
"""
Created on Sun May 17 10:58:17 2015

@author: aaronpayne
"""
# https://github.com/alexis-mignon/python-flickr-api/wiki/Tutorial
import flickr_api, argparse, yaml, os
from helper import get_paths, dumpclean
from photo import photo
from photo_manager import photo_manager

debug = True

def main():
    yaml_config_dict = setup_arguments()
    initialize_flickr(yaml_config_dict)
    pmanager = photo_manager(yaml_config_dict)
    sync_local_photos(yaml_config_dict, pmanager)
    pmanager.close()
    
def sync_local_photos(yaml_config_dict, pmanager):
    print 'Syncing local photos...'
    supported_photo_types = yaml_config_dict['supported_photo_types']
    for photo_directory in yaml_config_dict['photo_directories']:
        print ' - Syncing directory: '+photo_directory
        process_directory(photo_directory, pmanager, supported_photo_types)
            
        #flickr_api.upload(photo_file = "IMG_6481.JPG", title = "IMG_6481.JPG")
            
def process_directory(directory, pmanager, file_types):
    file_paths, directory_paths = get_paths(directory)
    for file_path in file_paths:
        fname, extension = os.path.splitext(file_path)
        extension = extension.replace('.', '')
        if extension in file_types:
            sync_local_photo(file_path, pmanager)
    for dir_path in directory_paths:
        process_directory(dir_path, pmanager, file_types)
        
def sync_local_photo(photo_path, pmanager):
    """
    http://stackoverflow.com/questions/2104080/how-to-check-file-size-in-python
    """
    local_photo = photo(photo_path)
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