# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 19:33:39 2015

@author: root
"""

import argparse, yaml, os
from helper import dumpclean

debug = False

def setup_arguments():
    print 'Setting up and parsing arguments...'
    ap = argparse.ArgumentParser()
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
        
    if "working_directory" in yaml_config:
        empty_working_directory(yaml_config["working_directory"], yaml_config["supported_photo_types"])
        
    return yaml_config

def empty_working_directory(directory_path, file_types):
    if debug:
        print 'Emptying working directory: '+directory_path
    # http://stackoverflow.com/questions/185936/delete-folder-contents-in-python
    for the_file in os.listdir(directory_path):
        file_path = os.path.join(directory_path, the_file)
        try:
            if os.path.isfile(file_path):
                for file_type in file_types:
                    if file_path.endswith(file_type):
                        os.unlink(file_path)
            #elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception, e:
            print e