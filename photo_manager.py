# -*- coding: utf-8 -*-
"""
Created on Wed May 20 20:05:03 2015

@author: root
"""

import sqlite3 as lite, os, datetime

from photo import photo, db_photo

debug = False

db_entry_fields = "id, fid, local_path, extension, size, modified_time, image_hash"

class photo_manager(object):
    """
    http://zetcode.com/db/sqlitepythontutorial/
    """
    def __init__(self, yaml):
        path = yaml["photo_info_db"]
        self.log = open(yaml["photo_manager_log"], "w")        
        if os.path.exists(path):
            self.db = lite.connect(path)
            self.cursor = self.db.cursor()
        else:
            print 'Database file did not exist, so creating a new one: '+path            
            self._create_blank_db(path)
        self._tag_dict = dict()
        self._read_tags()
        self.start_time = datetime.datetime.now()
        
    def get_photo_count(self):
        sql = "SELECT COUNT(id) FROM photo"
        return self._get_single_result(sql)
        
    def check_id(self, pid):
        sql = "SELECT name FROM photo WHERE fid="+str(pid)
        photo_check = self._get_single_result(sql)
        if photo_check == None:
            return False
        else:
            return photo_check
        
    def _read_tags(self):
        sql = "SELECT enum, label FROM tag_enum"
        results = self._get_multiple_results(sql)
        if results != None:
            for result in results:
                self._tag_dict[result[1]] = result[0] #key: label, value: enum
            
    def _add_tag(self, tag):
        if tag not in self._tag_dict:
            if debug:
                print "New tag: "+tag
            new_enum = self._generate_tag_enum()
            self._tag_dict[tag] = new_enum
            sql = "INSERT INTO tag_enum (enum, label) VALUES(?, ?)"
            self._execute(sql, args=(new_enum, tag))
            return new_enum
            
    def _create_blank_db(self, path):
        self.db = lite.connect(path)
        self.cursor = self.db.cursor()  
        self.cursor.executescript("""
            CREATE TABLE photo(id INT, originally_found INT, size INT, image_hash TEXT, 
                               local_path TEXT, extension TEXT, modified_time REAL, 
                               download_time REAL, last_touch REAL, name TEXT, 
                               fid INT, public INT, family INT, friends INT, 
                               upload_time REAL, reset_tags INT, archived INT);
            CREATE TABLE tag_enum(enum INT, label TEXT);
            CREATE TABLE tag_map(tag_enum INT, photo_id INT);
            """)
        self.db.commit()
        
    def reset_tags(self, uid, tag_list):
        self.unflag_tag_reset(uid)
        self.clear_tags(uid)
        self._add_tag_list(uid, tag_list)
        
    def clear_tags(self, uid):
        """
        http://www.w3schools.com/sql/sql_delete.asp
        """
        sql = "DELETE FROM tag_map WHERE photo_id=?"
        self._execute(sql, args=(uid,))            
        
    def add_local_photo(self, lphoto):
        local_already_present = self.check_for_path(lphoto)
        attribute_matches = self.check_for_attributes(lphoto)
        # If it isn't the exact same file, check the attributes
        
        if local_already_present != None:
            if debug:
                print 'Local file path already exists in the DB! '+lphoto.photo_path
            #exit()
            return
            
        elif attribute_matches != None:
            if debug:
                print 'A local image with a different path already exists in the database'
            self.log.write('Possible duplicate Image: '+str(lphoto))
            if len(attribute_matches) == 1:
                if debug:
                    print 'There was only 1 attribute match'
                # Check to see if the file has moved
                photo_match = attribute_matches[0]
                if not os.path.exists(photo_match.photo_path) and not self._is_archived(photo_match.uid):
                    self._update_local_path(photo_match.uid, lphoto.photo_path)
            else:
                for match in attribute_matches:
                    self.log.write('Existing Image: '+str(db_photo(db_entry=match)))
                #exit()
            return
            
        else:
            self.insert_photo(0, lphoto.size, lphoto.hash, tags=lphoto.tags, 
                              name=lphoto.filename, local_path=lphoto.photo_path, 
                              extension=lphoto.extension, time=lphoto.modified_time)
                              
    def _update_local_path(self, uid, new_path):
        if debug:
            print 'Updating local path...'
        sql = "UPDATE photo SET local_path=? WHERE id=?"
        self._execute(sql, (new_path, uid))
        self.flag_tag_reset(uid)
    
    def _is_archived(self, uid):
        sql = "SELECT id FROM photo WHERE id=? AND archived=1"
        args = (uid,)
        if self._get_single_result(sql, args) != None:
            return True
        return False
        
    def archive(self, uid):
        sql = "UPDATE photo SET archived=1 WHERE id=?"
        self._execute(sql, args=(uid,))
            
    def add_flickr_photo(self, flickr_photo, flickr_local_dir):
        if not self.flickr_photo_exists(flickr_photo):
            move_success = flickr_photo.move_flickr_to_local(flickr_local_dir)
            if move_success:
                uid = self.insert_photo(1, flickr_photo.size, flickr_photo.hash, tags=flickr_photo.tags, 
                                  name=flickr_photo.filename, local_path=flickr_photo.photo_path, 
                                  extension=flickr_photo.extension, time=flickr_photo.modified_time,
                                  dtime=flickr_photo.download_time, public=flickr_photo.ispublic,
                                  family=flickr_photo.isfamily, friends=flickr_photo.isfriend,
                                  fid=flickr_photo.fid)
                self.flag_tag_reset(uid)
        
    def flag_tag_reset(self, uid, flag_value=1):
        sql = "UPDATE photo SET reset_tags=? WHERE id=?"
        self._execute(sql, (flag_value, uid))
        
    def unflag_tag_reset(self, uid):
        self.flag_tag_reset(uid, flag_value=0)
        
    def get_photos_tag_reset(self):
        sql = "SELECT "+db_entry_fields+" FROM photo WHERE reset_tags=1"
        return self._get_multiple_photos(sql)
    
    def flickr_photo_exists(self, fphoto):
        attribute_matches = self.check_for_attributes(fphoto)
        # If it isn't the exact same file, check the attributes
        if attribute_matches != None:
            print 'A local image with the same hash already exists in the database'
            self.log.write('Possible duplicate Image: '+str(fphoto))
            for match in attribute_matches:
                self.log.write('Existing Image: '+str(match))
            #exit()
            return True
        return False
            
    def _string_found(self, found_value):
        if found_value == 0:
            return "Originally Local"
        elif found_value == 1:
            return "Originally Flickr"
        else:
            print 'ERROR: Bad found value:'+str(found_value)
            exit()
            
    def insert_photo(self,
                     found,
                     size,
                     ihash,
                     local_path=None,
                     extension=None,
                     time=None,
                     dtime=None,
                     name=None,
                     fid=None,
                     public=None,
                     family=None,
                     friends=None,
                     utime=None,
                     reset_tags=0,
                     archived=0,
                     tags=None):
        """
        http://stackoverflow.com/questions/17169642/python-sqlite-insert-named-parameters-or-null
        """
        uid = self._generate_photo_id()
        # http://stackoverflow.com/questions/415511/how-to-get-current-time-in-python
        sql = "INSERT INTO photo VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        values = (uid, found, size, ihash, 
                  local_path, extension, time, dtime, self.start_time,
                  name, fid, public, family, friends, utime, reset_tags, archived)
        self._execute(sql, args=values)
        if tags != None:
            if debug:
                print 'There are tags'
            self._add_tag_list(uid, tags)
        return uid
        
    def _add_tag_list(self, uid, tag_list):
        tag_additions = list()
        for tag in tag_list:
            if tag not in self._tag_dict:
                tag_enum = self._add_tag(tag)
            else:
                tag_enum = self._tag_dict[tag]
            # http://stackoverflow.com/questions/1380860/add-variables-to-tuple
            tag_additions.append((tag_enum, uid))
        sql = "INSERT INTO tag_map VALUES(?, ?)"
        self._execute_many(sql, tag_additions)
                     
    def _generate_photo_id(self):
        return self._generate_id("photo", "id")
        
    def _generate_tag_enum(self):
        return self._generate_id("tag_enum", "enum")
        
    def _generate_id(self, table, field):
        sql = "SELECT MAX("+field+") FROM "+table
        new_id = self._get_single_result(sql)
        if new_id == None:
            new_id = 0
        else:
            new_id = new_id+1
        if debug:
            print 'Generated new ID :'+str(new_id)
        return new_id
            
    def _execute(self, sql, args=None):
        """
        http://stackoverflow.com/questions/16856647/sqlite3-programmingerror-incorrect-number-of-bindings-supplied-the-current-sta
        """        
        if debug:
            print 'Executing SQL: '+sql
        if args != None:
            self.cursor.execute(sql, args)
        else:
            self.cursor.execute(sql)
        self.db.commit()
            
    def _execute_many(self, sql, args=None):
        if debug:
            print 'Executing multilple SQL: '+sql
        if args == None:
            print 'ERROR: execute_many must have non-None args'
            exit()
        self.cursor.executemany(sql, args)
        self.db.commit()
        
    def local_photo_exists(self, lphoto):
        local_already_present = self.check_for_path(lphoto)
        attribute_matches = self.check_for_attributes(lphoto)
        # If it isn't the exact same file, check the attributes
        if local_already_present != None:
            if debug:
                print 'Local file path already exists in the DB! '+lphoto.photo_path
            #exit()
            return True
        elif attribute_matches != None:
            print 'A local image with a different path already exists in the database'
            self.log.write('Possible duplicate Image: '+str(lphoto))
            for match in attribute_matches:
                self.log.write('Existing Image: '+str(db_photo(db_entry=match)))
            #exit()
            return True
        return False
        
    def check_for_path(self, lphoto):
        sql = "SELECT local_path, modified_time, size, image_hash FROM photo WHERE local_path=?"
        result = self._get_multiple_results(sql, args=(lphoto.photo_path,))
        if result != None:
            self._update_last_touch("local_path", lphoto.photo_path)
        return result
        
    def _update_last_touch(self, field, value):
        sql = "UPDATE photo SET last_touch=? WHERE "+field+"=?"
        self._execute(sql, (self.start_time, value))
    
    def check_for_attributes(self, photo_obj):
        """ 
        """
        sql= "SELECT "+db_entry_fields+" FROM photo WHERE size=? AND image_hash=?"
        return self._get_multiple_photos(sql, args=(photo_obj.size, photo_obj.hash))
        
    def _get_single_result(self, sql, args=None):
        self._execute(sql, args)
        result = self.cursor.fetchone()
        if result == None:
            return None
        else:
            return result[0]
    
    def _get_multiple_results(self, sql, args=None):
        self._execute(sql, args)        
        rows = self.cursor.fetchall()
        if len(rows) > 0:
            return rows
        else:
            return None
            
    def get_photo_tags(self, photo_id):
        sql = "SELECT te.label FROM ((SELECT * FROM tag_map WHERE photo_id=?) AS tm LEFT JOIN tag_enum AS te ON tm.tag_enum=te.enum)"
        args = (photo_id,)
        results = self._get_multiple_results(sql, args)
        return_list = list()
        for result in results:
            return_list.append(result[0])
        return return_list
            
    def get_photos_to_upload(self):
        """
        http://www.w3schools.com/sql/sql_null_values.asp
        """
        sql = "SELECT "+db_entry_fields+" FROM photo WHERE originally_found=0 AND upload_time IS NULL"
        return self._get_multiple_photos(sql)
        
    def _get_multiple_photos(self, sql, args=None):
        results = self._get_multiple_results(sql, args)
        return_photo_list = list()
        if results == None:
            return None
        for result in results:
            return_photo_list.append(db_photo(db_entry=result))
        return return_photo_list
        
    def add_upload_data(self, data):
        """
        http://www.w3schools.com/sql/sql_update.asp
        """
        if debug:
            print 'Adding upload data:'
            print 'photo_id: '+str(data['fid'])
        sql = "UPDATE photo SET fid=?, public=?, family=?, friends=?, upload_time=? WHERE local_path=?"
        args = (data['fid'], data['public'], data['family'], data['friend'], data['upload_time'], data['path'])
        self._execute(sql, args)
            
    def close(self):
        self.db.close()
        self.log.close()