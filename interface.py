# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 19:33:39 2015

@author: root
"""

import argparse, yaml, os
from helper import dumpclean

debug = False

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
