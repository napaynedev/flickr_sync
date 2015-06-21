# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 19:26:38 2015

@author: root
"""

import sys
if __name__ == '__main__':
    if __package__ is None:
        from os import path
        sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
        from flickr_functions import flickr
        from interface import setup_arguments
        from photo import photo
    else:
        from ..flickr_functions import flickr
        from ..interface import setup_arguments
        from ..photo import photo

def main():
    test_photo_path = 'testphotos/IMG_0729.JPG'
    print 'Test photo path: '+test_photo_path
    yaml_config_dict = setup_arguments()
    flickr_controller = flickr(yaml_config_dict)
    print '\nUploading photo...'
    upload_dict = flickr_controller.upload_photo(photo(local_photo=test_photo_path), ['0:first', '1:second', '2:third'], yaml_config_dict["photo_permissions"])
    fid = upload_dict['fid']
    print '\nUploaded photo received id: '+str(fid)
    flickr_controller.print_photos([fid])
    print '\nAdding more tags'
    flickr_controller.add_tags(fid, ['3:fourth', '4:fifth'])
    flickr_controller.print_photos([fid])
    print '\nRemoving all tags'
    flickr_controller.remove_all_tags(fid)
    flickr_controller.print_photos([fid])
    print '\nAdding more tags including one that is not special'
    flickr_controller.add_tags(fid, ['5:sixth', 'delete'])
    flickr_controller.print_photos([fid])
    print '\nRemoving tags again'
    flickr_controller.remove_all_tags(fid)
    flickr_controller.print_photos([fid])

if __name__ == "__main__":
    main()