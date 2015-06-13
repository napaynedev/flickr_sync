# -*- coding: utf-8 -*-
"""
Created on Wed May 20 20:05:03 2015

@author: root
"""

import sqlite3 as lite, os

debug = True

class photo_manager(object):
    """
    http://zetcode.com/db/sqlitepythontutorial/
    """
    def __init__(self, yaml):
        path = yaml["photo_info_db"]        
        if os.path.exists(path):
            self.db = lite.connect(path)
            self.cursor = self.db.cursor()
        else:
            print 'Database file did not exist, so creating a new one: '+path            
            self._create_blank_db(path)
        self._tag_dict = dict()
        self._read_tags()
        
    def _read_tags(self):
        sql = "SELECT enum, label FROM tag_enum"
        results = self._get_multiple_results(sql)
        if results != None:
            for result in results:
                self._tag_dict[result[1]] = result[0] #key: label, value: enum
            
    def _add_tag(self, tag):
        new_enum = self._generate_tag_enum()
        self._tag_dict[new_enum] = tag
        sql = "INSERT INTO tag_enum VALUES(?, ?)"
        self._execute(sql, args=(new_enum, tag))
        return new_enum
            
    def _create_blank_db(self, path):
        self.db = lite.connect(path)
        self.cursor = self.db.cursor()  
        self.cursor.executescript("""
            CREATE TABLE photo(id INT, originally_found INT, size INT, image_hash TEXT, 
                               local_path TEXT, extension TEXT, modified_time REAL, download_time REAL,
                               name TEXT, fid INT, public INT, family INT, friends INT, upload_time REAL);
            CREATE TABLE tag_enum(enum INT, label TEXT);
            CREATE TABLE tag_map(tag_enum INT, photo_id INT);
            """)
        self.db.commit()
        
    def add_local_photo(self, photo):
        if self.local_photo_exists(photo):
            print 'ERROR: Local file already exists: '+photo.name
        else:
            self.insert_photo(0, photo.size, photo.hash, local_path=photo.photo_path, extension=photo.extension, time=photo.modified_time)
            
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
                     tags=None):
        """
        http://stackoverflow.com/questions/17169642/python-sqlite-insert-named-parameters-or-null
        """
        uid = self._generate_photo_id()
        sql = "INSERT INTO photo VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        values = (uid, found, size, ihash, local_path, extension, time, dtime, 
                  name, fid, public, family, friends, utime)
        self._execute(sql, args=values)
        tag_additions = ()
        if tags != None:
            for tag in tags:
                if tag not in self._tag_dict:
                    tag_enum = self._add_tag(tag)
                else:
                    tag_enum = self._tag_dict[tag]
                # http://stackoverflow.com/questions/1380860/add-variables-to-tuple
                tag_additions = tag_additions +((tag_enum, uid))
            sql = "INSERT INTO tag_map VALUES(?, ?)"
            self._execute_many(sql, tag_additions)        
                     
    def _generate_photo_id(self):
        sql = "SELECT MAX(id) FROM photo"
        new_id = self._get_single_result(sql)
        if new_id == None:
            new_id = 0
        else:
            new_id = new_id+1
        if debug:
            print 'Generated new ID :'+str(new_id)
        return new_id
        
    def _generate_tag_enum(self):
        return self._generate_id("tag_enum", "enum")
        
    def _generate_id(self, table, field):
        sql = "SELECT MAX(?) FROM ?"
        return self._get_single_result(sql, args=(field, table))
            
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
        if args == None:
            print 'ERROR: execute_many must have non-None args'
            exit()
        self.cursor.executemany(sql, args)
        self.db.commit()
        
    def local_photo_exists(self, photo):
        local_already_present = self.check_for_path(photo)
        if local_already_present != None:
            print 'Local file path already exists in the DB! '+photo.photo_path
            exit()
            return True
        attribute_matches = self.check_for_attributes(photo)
        if attribute_matches != None:
            print 'In image with these attributes already exists in the database'
            exit()
            return True
        return False
        
    def check_for_path(self, photo):
        sql = "SELECT local_path, modified_time, size, image_hash FROM photo WHERE local_path=?"
        return self._get_multiple_results(sql, args=(photo.photo_path,))
    
    def check_for_attributes(self, photo):
        sql= "SELECT local_path, originally_found, id FROM photo WHERE size=? AND image_hash=?"
        return self._get_multiple_results(sql, args=(photo.size, photo.hash))
        
    def _get_single_result(self, sql, args=None):
        self._execute(sql, args)
        return self.cursor.fetchone()[0]
                                                                  
    def _get_multiple_results(self, sql, args=None):
        self._execute(sql, args)        
        rows = self.cursor.fetchall()
        if len(rows) > 0:
            return rows
        else:
            return None
            
    def close(self):
        self.db.close()