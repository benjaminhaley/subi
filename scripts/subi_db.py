#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import sqlite3 as lite
from sqlite3 import dump    # Need to be explicit for py2exe to work
import sys
import os
import time
import string
import codecs

class subi_db_class:
    connection = None
    acceptable_col_types = ['VARCHAR(120)', 'DECIMAL(10,10)', 'BOOL']

    #   basic functions
    def __init__(self,
            data_dir='data',
            db_filename='subi.db',
            backup_prefix='subi_backup'
            ):
        self.data_dir = data_dir
        self.db_filename = db_filename
        self.backup_prefix = backup_prefix
        self.db_path = os.path.join(data_dir, db_filename)
        self.connection = lite.connect(self.db_path)
        if self.__tables_exist() == False:
            self.__create_tables()

    def close(self):
        self.connection.close()

    #   start-up functions (only run once)
    def __tables_exist(self):
        connection = self.connection
        cursor = connection.cursor()
        TABLES_EXIST = False

        cursor.execute("""SELECT name
                          FROM   sqlite_master
                          WHERE  (name = 'animals' OR name = 'col_definitions')
                          AND    type = 'table';
                          """)
        rows = cursor.fetchall()
        if len(rows) == 2:
            TABLES_EXIST = True
        else:
            TABLES_EXISTS = False
        return TABLES_EXIST

    def __create_tables(self):
        connection = self.connection
        cursor = connection.cursor()
        cursor.execute("""CREATE TABLE animals
                          (animal_id varchar(12) primary key);
                          """)
        connection.commit()

        # we will make the col_order the primary key
        # which forces it to auotincrement.
        # Also we actually don't want the autoincrement keyword
        # because it makes that key unique forever.  So we could
        # never switch two ordinals.
        # see
        #   http://www.sqlite.org/autoinc.html
        cursor.execute("""CREATE TABLE col_definitions
                          (col_name varchar(12) unique,
                           col_description varchar(12),
                           col_type varchar(12),
                           col_order integer primary key,
                           col_group varchar(12),
                           active bool);
                          """)
        connection.commit()

        cursor = connection.cursor()
        cursor.execute("""  INSERT INTO col_definitions
                            (col_name, col_description, col_type, col_group, active)
                            VALUES
                            ('animal_id', 'Animal ID', 'DECIMAL(10,10)', '', 1);""")
        connection.commit()

    #   column functions
    def __column_names(self):
        import sqlite3 as lite
        connection = self.connection
        col_names = []

        #   this will allow the data to get returned as a dictionary
        connection.row_factory = lite.Row
        cursor = connection.cursor()
        cursor.execute("""SELECT col_name
                          FROM   col_definitions
                          WHERE  active = 1;
                          """)
        rows = cursor.fetchall()
        for row in rows:
            col_names.append(row[0])
        return col_names

    def __validate_col_name(self, col_name):
        #   only allow letters and underscores
        col_name = col_name.replace("_", "")
        IS_VALID = col_name.isalpha()
        if not IS_VALID:
            raise Exception("""Column names can be letters or underscores,
                                %s was passed in.""" % col_name)

    def __column_types(self):
        col_list = list()

        connection = self.connection
        cursor = connection.cursor()
        cursor.execute("""pragma table_info(animals);""")
        rows = cursor.fetchall()
        for row in rows:
            col_list.append(row[2])
        return col_list

    def __col_exists(self, col_name):
        col_list = self.__column_names()
        col_name_as_list = [col_name]
        COL_EXISTS = [i for i in col_list if i in col_name_as_list]
        return COL_EXISTS

    def __validate_col_type(self, col_type):
        if col_type not in self.acceptable_col_types:
            raise Exception('col_type must fit one of acceptable data types.')
        return True

    def __clean_search_string(self, search_string):
        # Remove special characters
        safe_term = "".join(
                [c for c in search_string
                if c.isalpha() or c.isdigit() or c == ' ']
            )
        return safe_term

    def col_info(self, col_name=None):
        #   Returns a list of dictionary row objects
        #   If col_name is passed in,
        #   only definitions for that column are returned
        #   otherwise, all are returned
        import sqlite3 as lite

        connection = self.connection
        connection.row_factory = lite.Row
        cursor = connection.cursor()

        sql_str = ''
        if col_name == None:
            cursor.execute("""SELECT *
                              FROM   col_definitions
                              WHERE  active = 1
                              ORDER BY col_order
                           """, []
                          )
        else:
            cursor.execute("""SELECT *
                              FROM   col_definitions
                              WHERE  active = 1
                              AND col_name =?
                              ORDER BY col_order
                              """, [col_name]
                          )

        rows = cursor.fetchall()

        # Change into a dictionary
        result = []
        for r in rows:
            row_dict = {}
            for key in r.keys():
                row_dict[key] = r[key]
            result.append(row_dict)

        return result

    def create_col(self, col_name, col_type, col_description, col_group=None):
        # check for injection
        self.__validate_col_name(col_name)
        self.__validate_col_type(col_type)
        if self.__col_exists(col_name):
            raise Exception('Column already exists')
        connection = self.connection

        sql_args = [col_name, col_description, col_type, col_group]
        cursor = connection.cursor()
        cursor.execute("""  INSERT INTO col_definitions
                            (col_name, col_description, col_type, col_group, active)
                            VALUES
                            (?, ?, ?, ?, 1);
                            """, sql_args)
        connection.commit()

        #  add columnn to animals table
        sql_args = col_name, col_type
        cursor = connection.cursor()
        # injection avoided above
        cursor.execute(""" ALTER TABLE animals
                           ADD %s %s;""" % sql_args)
        connection.commit()

    def update_col(self, col_name, field_name, field_value):

        # Check column and field names to avoid injection
        if not self.__col_exists(col_name):
            raise Exception("Column does not exist: " + col_name)
        valid_fields = ['col_description', 'col_type', 'col_group', 'col_name']
        if not field_name in valid_fields:
            raise Exception("field_name is not valid")

        # used for name update (ugly) see below
        old_col_names = self.__column_names()
        old_col_sql = string.joinfields(old_col_names,sep=",")

        #   update column in column_definitions table
        connection = self.connection
        cursor = connection.cursor()
        connection.commit()
        cursor.execute("""  UPDATE  col_definitions
                            SET     %s = ?
                            WHERE   col_name LIKE "%s";""" % (field_name, col_name),
                            [field_value])
        connection.commit()
        # if the column name was changed update the animal table
        # Note you have to copy the whole database to to this (ugly)
        # see
        #   http://stackoverflow.com/questions/805363/how-do-i-rename-a-column-in-a-sqlite-database-table
        if field_name == "col_name":
            #   this is used for the insert select query during col renaming
            new_col_info_rows = self.col_info()
            new_col_list = []
            for col_entry in new_col_info_rows:
                col_entry_name = col_entry['col_name']
                col_entry_type = col_entry['col_type']
                col_entry_list = [col_entry_name, col_entry_type]
                new_col_list.append(string.joinfields(col_entry_list, sep=" "))
            new_col_creation_sql = string.joinfields(new_col_list, sep=", ")

            new_col_names = self.__column_names()
            new_col_insertion_sql = string.joinfields(new_col_names, sep=",")

            # Try to drop first in case a copy was left behing in a
            # broken test run
            try:
                cursor.execute("""  DROP TABLE temp_animals;""")
            except:
                pass

            cursor = connection.cursor()
            cursor.execute("""  ALTER TABLE animals RENAME to temp_animals;""")

            cursor = connection.cursor()
            cursor.execute("""  CREATE TABLE animals
                                (%s);
                                """ % new_col_creation_sql)
                                # injection avoided at the top

            sql_args = new_col_insertion_sql, old_col_sql
            cursor.execute("""  INSERT INTO animals
                                (%s)
                                SELECT  %s
                                FROM    temp_animals;
                                """ % sql_args)  # injection avoided at the top

            cursor.execute("""  DROP TABLE temp_animals;""")
            connection.commit()

    def delete_col(self, col_name):
        #   check column name to avoid injection
        if not self.__col_exists(col_name):
            raise Exception("Column does not exist: " + col_name)

        #   update the column defs table
        connection = self.connection
        cursor = connection.cursor()
        cursor.execute("""  DELETE FROM col_definitions
                            WHERE   col_name = ?;""", [col_name])
        connection.commit()

        #   update the animals table
        #   this is used for the insert select query
        import string
        new_col_info_rows = self.col_info()
        new_col_list = []
        for col_entry in new_col_info_rows:
            col_entry_name = col_entry['col_name']
            col_entry_type = col_entry['col_type']
            col_entry_list = [col_entry_name, col_entry_type]
            new_col_list.append(string.joinfields(col_entry_list, sep=" "))
        new_col_creation_sql = string.joinfields(new_col_list, sep=", ")

        new_col_names = self.__column_names()
        new_col_insertion_sql = string.joinfields(new_col_names, sep=",")

        cursor = connection.cursor()
        cursor.execute("""  ALTER TABLE animals RENAME to temp_animals;""")
        cursor = connection.cursor()

        # injection avoided above
        cursor.execute("""  CREATE TABLE animals
                            (%s);
                            """ % new_col_creation_sql)

        sql_args = new_col_insertion_sql, new_col_insertion_sql
        cursor.execute("""  INSERT INTO animals
                            (%s)
                            SELECT  %s
                            FROM    temp_animals;
                            """ % sql_args)        # injection avoided above

        cursor.execute("""  DROP TABLE temp_animals;""")
        connection.commit()

    #   animal functions
    def insert_new_animal(self, animal_id):
        if self.animal_exists(animal_id):
            raise Exception("Animal id already in database")
        connection = self.connection
        cursor = connection.cursor()
        cursor.execute(""" INSERT INTO animals (animal_id)
                           VALUES (?);
                          """, [animal_id])
        connection.commit()

    def animal_exists(self, animal_id):
        # If the animal exists we will get a result
        if len(self.lookup_animal(animal_id)) > 0:
            return True
        else:
            return False

    def update_animal_field(self, animal_id, col_name, col_value):

        # Explicitly check for column to prevent sql injection
        if not self.__col_exists(col_name):
            raise Exception("Column does not exist: " + col_name)

        # Check if the animal actually exists
        if not self.animal_exists(animal_id):
            raise Exception("Could not find animal id to update")

        connection = self.connection
        cursor = connection.cursor()
        sql_args = [col_value, animal_id]
        # injection prevented above
        cursor.execute(""" UPDATE animals
                           SET    %s = ?
                           WHERE  animal_id = ?;
                           """ % col_name, sql_args)
        connection.commit()

    def delete_animal(self, animal_id):
        connection = self.connection
        cursor = connection.cursor()
        cursor.execute(""" DELETE FROM animals
                           WHERE  animal_id = ?;
                           """, [animal_id])
        # Check that an animal was deleted
        if(cursor.rowcount == 0):
            raise Exception("No animals found with id: " + animal_id)
        connection.commit()

    def copy_animal(self, origin_id, copy_id):
        # Lookup animal first, so we fail if it is not found
        original = self.lookup_animal(origin_id)[0]

        # Instantiate the new animal and fill in its values
        self.insert_new_animal(copy_id)
        for key in original.keys():
            if key != 'animal_id':
                self.update_animal_field(copy_id, key, original[key])

    def lookup_animal(self, animal_id):
        import sqlite3 as lite
        connection = self.connection

        #   this will allow the data to get returned as a dictionary
        connection.row_factory = lite.Row
        cursor = connection.cursor()
        cursor.execute("""SELECT *
                          FROM   animals
                          WHERE  animal_id = ?;
                          """, [animal_id])
        rows = cursor.fetchall()
        if len(rows) > 1:
            raise Exception("More than one matching animal_id was found. They should be unique.")

        # Conform to the format of the search results, a list of dictionaries
        # Use a loop to handle the case where there are no matches
        # usually there will be one and never more.
        animals = []
        for r in rows:
            animal_dict = {}
            for key in r.keys():
                animal_dict[key] = r[key]
            animals.append(animal_dict)

        return animals

    def get_unique_col_values(self, col_name, min_freq=1):
        # Return unique values from a column in the
        # animal table as a list.

        #   check column name to avoid injection
        if not self.__col_exists(col_name):
            raise Exception("Column does not exist: " + col_name)

        # force frequence to be an integer to avoid injection
        min_freq = int(min_freq)

        #   update the column defs table
        connection = self.connection
        cursor = connection.cursor()

        # injection avoided above
        cursor.execute("""
                    SELECT %s
                    FROM animals
                    GROUP BY %s
                    HAVING COUNT(*) >= %s;""" % (col_name, col_name, min_freq))
        rows = cursor.fetchall()

        # convert result to a list
        values = []
        for r in rows:
            values.append(r[0])

        return values

    def search_fulltext(self, search_terms=[], offset=0, limit=10):
        # Free text search
        # Expects a list of search terms and Returns the number of matches
        # and a list of dictionaries representing those animals which matched
        # each search term in one field or another.

        # Template the results
        result = {}
        result['animals'] = []
        result['count'] = 0

        print search_terms
        # Make sure the query is safe
        safe_terms = []
        for term in search_terms:
            safe_term = self.__clean_search_string(term)
            safe_terms.append(safe_term)

        columns = self.__column_names()

        # Construct the where clause
        WHERE = '1 == 1 '               # an always true statement
                                        # so we can plan an 'and' on every line
        for t in safe_terms:
            WHERE += 'and ((1 == 0) '   # an always false statement (see above)
            for c in columns:
                WHERE += ' or (`' + c + '` LIKE "%' + t + '%")'
            WHERE += ')'

        # get animal results
        connection = self.connection
        cursor = connection.cursor()
        rows = cursor.execute(
                """ SELECT *
                    FROM animals
                    WHERE %s
                    ORDER BY animal_id
                    LIMIT ?, ?
                """ % WHERE, (offset, limit))

        # tranlsate to dictionary
        for r in rows:
            animal = {}
            for key in r.keys():
                animal[key] = r[key]
            result['animals'].append(animal)

        # get count results
        connection = self.connection
        cursor = connection.cursor()
        rows = cursor.execute(
                """ SELECT COUNT(animal_id)
                    FROM animals
                    WHERE %s
                """ % WHERE)

        for r in rows:
            result['count'] = r[0]

        return result

    #   return a set of lists with all of the active (non-deleted) animal data
    def run_sql_query(self, sql_string):
        import sqlite3 as lite
        connection = self.connection
        #   this will allow the data to get returned as a dictionary
        connection.row_factory = lite.Row
        cursor = connection.cursor()
        try:
            cursor.execute(""" %s; """ % sql_string)
        except:
            cursor.executescript(""" %s; """ % sql_string)
        rows = cursor.fetchall()
        return rows

    def backup_db(self):
        # Dump the database to a file
        # and return the filename
        connection = self.connection
        dump = ''

        # sortable, non conflicting, and timely
        # e.g. 'subi_dump_1326494589.03'
        filename = '%s_%s' % (
                        self.backup_prefix,
                        str(time.time())
                        )
        filepath = os.path.join(self.data_dir, filename)

        # use utf-8 to support unicode
        f = codecs.open(filepath, encoding='utf-8', mode='w')
        for line in connection.iterdump():
            f.write('%s\n' % line)
        f.close()

        return filename

    def list_backups(self):
        """ Return a list of backup dictionaries
            including the backup name and filesize
            in bytes.
        """
        datafiles = os.listdir(self.data_dir)
        backups = [f for f in datafiles if f.startswith(self.backup_prefix)]
        backup_list = []
        for b in backups:
            filepath = os.path.join(self.data_dir, b)
            backup_list.append({'filename': b,
                                'bytes': os.path.getsize(filepath)})

        return backup_list

    def load_db(self, filename):
        # load a new db from a saved one
        # and make a backup of the current db
        # return the filename of the new backup

        # could be insecure if the saved db is corrupt
        connection = self.connection

        # check to see that backup exists and is valid
        db_list = self.list_backups()
        db_filenames = [db['filename'] for db in db_list]
        is_valid_backup_name = (filename in db_filenames)
        if not is_valid_backup_name:
            raise Exception("Database filename could not be found")

        # open the backup file first.
        # that way an error will get thrown before any deleting happens if
        # it cannot be found.
        filepath = os.path.join(self.data_dir, filename)
        backup = codecs.open(filepath, encoding='utf-8', mode='r')

        # make a new backup file just in case
        backup_filename = self.backup_db()

        # remove the current db
        self.drop_tables()

        # instantiate the new db
        self.run_sql_query(backup.read())

        # return the freshly made backup
        return backup_filename

    def delete_backup(self, filename):
        # Delete a backuped database
        connection = self.connection

        # check to see that backup exists and is valid
        db_list = self.list_backups()
        db_filenames = [db['filename'] for db in db_list]
        is_valid_backup_name = (filename in db_filenames)
        if not is_valid_backup_name:
            raise Exception("Database filename could not be found")

        filepath = os.path.join(self.data_dir, filename)
        os.remove(filepath)

    #   functions to be used for testing only
    def drop_tables(self):
        connection = self.connection
        cursor = connection.cursor()
        try:
            cursor.execute("""DROP TABLE animals;""")
            connection.commit()
        except:
            pass
        try:
            cursor.execute("""DROP TABLE col_definitions;""")
            connection.commit()
        except:
            pass


class subi_db_integration_test:
    def non_unique_insert(self, subi_db_object):
        import random
        rand_id = random.randint(100000000, 99999999999)
        try:
            subi_db_object.insert_new_animal(rand_id)
            subi_db_object.insert_new_animal(rand_id)
        except Exception as e:
            if e.message == "Animal id already in database":
                pass
            else:
                raise Exception('non_unique_insert test failed!')

    def animal_update_and_lookup(self, subi_db_object):
        import random

        #   test insertion
        rand_id = unicode(random.randint(100000000, 99999999999))
        subi_db_object.insert_new_animal(rand_id)
        looked_up_row = subi_db_object.lookup_animal(rand_id)[0]
        if looked_up_row["animal_id"] != rand_id:
            raise Exception('Insert animal test failed.')

        #   create a column, then update the value for the inserted animal
        subi_db_object.create_col(
                'bee',
                'DECIMAL(10,10)',
                'this column is about turtles'
                )
        subi_db_object.update_animal_field(rand_id, 'bee', 2000)
        looked_up_row = subi_db_object.lookup_animal(rand_id)[0]
        if looked_up_row['bee'] != 2000:
            raise Exception('Update animal field test failed.')

    def delete_animal(self, subi_db_object):
        import random

        rand_id = unicode(random.randint(100000000, 99999999999))
        subi_db_object.insert_new_animal(rand_id)
        subi_db_object.delete_animal(rand_id)
        if len(subi_db_object.lookup_animal(rand_id)) != 0:
            raise Exception('Delete animal test failed.')
        else:
            pass

    def add_columns(self, subi_db_object):
        col_name = 'add_column_test_col'
        col_type = 'BOOL'
        col_description = 'Some boolean column'
        col_group = 'boolean items'
        subi_db_object.create_col(col_name, col_type, col_description, col_group)
        col_info = subi_db_object.col_info(col_name)
        for row in col_info:
            if row['col_type'] != col_type:
                raise Exception('col_type did not match')
            if row['col_description'] != col_description:
                raise Exception('col_description did not match')

    def add_duplicate_column_fails(self, subi_db_object):
        col_name = 'duplication_test_col'
        col_type = 'BOOL'
        col_description = 'Some boolean column'
        col_group = 'boolean items'
        subi_db_object.create_col(col_name, col_type, col_description, col_group)
        TEST_FAILED = False
        try:
            subi_db_object.create_col(col_name, col_type, col_description, col_group)
        except:
            TEST_PASSED = True
        if not TEST_PASSED:
            raise Exception("Adding a duplicate column did not raise an exception")

    def update_column(self, subi_db_object):
        col_name = 'update_test_col'
        col_type = 'BOOL'
        col_description = 'Some boolean column'
        col_group = 'boolean items'
        subi_db_object.create_col(col_name, col_type, col_description, col_group)

        # Make a few updates
        new_col_name = 'hamster'
        new_col_description = 'New column description'
        new_col_group = 'new group'
        subi_db_object.update_col(col_name, 'col_description', new_col_description)
        subi_db_object.update_col(col_name, 'col_name', new_col_name)
        subi_db_object.update_col(new_col_name, 'col_group', new_col_group)

        # Check if the updates are correct
        col_info = subi_db_object.col_info(new_col_name)
        for row in col_info:
            if row['col_type'] != col_type:
                raise Exception('col_type should be BOOL')
            if row['col_description'] != new_col_description:
                raise Exception('col_description did not match')
            if row['col_description'] != new_col_description:
                raise Exception('col_description did not match')

    def delete_column(self, subi_db_object):
        col_name = 'deletion_test'
        col_type = 'BOOL'
        col_description = 'Some boolean column'
        col_group = 'boolean items'
        subi_db_object.create_col(col_name, col_type, col_description, col_group)
        subi_db_object.delete_col(col_name)
        col_info = subi_db_object.col_info(col_name)
        if len(col_info) != 0:
            raise Exception('Column was not deleted!')

    def regular_use_pattern(self, subi_db_object):
        #   in __main__, you would instantiate subi_db_object
        #   subi_db_object = subi_db_class()

        #   get a list of the columns
        col_info = subi_db_object.col_info()

        #   add a column
        col_name = 'turle'
        col_type = 'BOOL'
        col_description = 'Some boolean column'
        col_group = 'boolean items'
        #   the column name gets returned
        subi_db_object.create_col(col_name, col_type, col_description, col_group)

        #   update the column to be in a different group
        col_type = 'BOOL'
        col_description = 'Some boolean column'
        col_group = 'new group name'
        subi_db_object.update_col(col_name, 'col_group', col_group)

        #   create a new animal
        import random
        rand_id = unicode(random.randint(100000000, 99999999999))
        subi_db_object.insert_new_animal(rand_id)

        #   update the animals' value for colname
        subi_db_object.update_animal_field(rand_id, col_name, 2000)

        #   look up the animal
        looked_up_row = subi_db_object.lookup_animal(rand_id)[0]

        #   delete the animal
        subi_db_object.delete_animal(rand_id)

        #   delete the column
        subi_db_object.delete_col(col_name)

        #   return all the rows from animal table
        all_rows = subi_db_object.run_sql_query("SELECT * FROM animals")

        #   here, you would close the connection
        #   subi_db_object.close()

    def search_fulltext(self, subi_db_object):
        # I should be able to fetch a list
        # of animals given certain constraints
        # NOT IMPLEMENTED FULLY
        result = subi_db_object.search_fulltext(search_terms=['2000'])
        if len(result['animals']) != 1:
            raise Exception('Fetched %s animals expected 1' % len(animals))
        if result['count'] != 1:
            raise Exception('Expected animal count to be one')

    def get_unique_col_values(self, subi_db_object):
        col_name = 'bee'

        # Test with min frequency of 1 (the default)
        expected = [None, 2000]
        results = subi_db_object.get_unique_col_values(col_name)
        if(results != expected):
            raise Exception(
                """get_unique_col_values test expected %s
                but got %s""" % (expected, results))

        # Test with min frequency of 2
        expected = []
        results = subi_db_object.get_unique_col_values(col_name, 2)
        if(results != expected):
            raise Exception(
                """get_unique_col_values test expected %s
                but got %s""" % (expected, results))



    def dump_and_restore(self, subi_db_object):
        # dump the database and then
        # check that the new backup is listed
        # kill the db and reload it from said backup.
        # Make sure the redump is the same as the first dump
        # Then delete the new backup and
        # finally check that the list is restored to its
        # original state.

        # Make a backup and prove its listed
        first_backup_list = subi_db_object.list_backups()
        first_backup = subi_db_object.backup_db()
        second_backup_list = subi_db_object.list_backups()
        is_listed = any(True for b in second_backup_list
                             if b['filename'] == first_backup
                       )
        if not is_listed:
            raise Exception("backup was not properly listed")

        # overwrite the current db
        # wait a jiff to be sure we dont have a name conflict
        import time
        time.sleep(0.02)
        second_backup = subi_db_object.load_db(first_backup)

        # compare the first and second dumps
        first_backup_path = os.path.join('data', first_backup)
        second_backup_path = os.path.join('data', second_backup)
        dump = open(first_backup_path).read()
        redump = open(second_backup_path).read()

        if dump != redump:
            raise Exception("You can't even take a dump right")

        # cleanup the backups we made
        subi_db_object.delete_backup(first_backup)
        subi_db_object.delete_backup(second_backup)

        # verify that we cleaned well
        third_backup_list = subi_db_object.list_backups()

        if len(first_backup_list) != len(third_backup_list):
            raise Exception("Newly created backups were not cleaned up")

    def animal_exists(self, test_subi_object):
        # Ensure the animal exists
        try:
            test_subi_object.insert_new_animal('23949830')
        except:
            pass

        # Assert the animal exists
        if test_subi_object.animal_exists('23949830') == False:
            raise Exception("Animal should exist and does not")

        # Delete the animal and be sure it no longer exists
        test_subi_object.delete_animal('23949830')

        # Assert the animal exists
        if test_subi_object.animal_exists('23949830') == True:
            raise Exception("Animal exists and should not")

    def copy_animal(self, test_subi_object):
        # Ensure the animal exists
        try:
            test_subi_object.insert_new_animal('23949830')
        except:
            pass

        # Make a copy
        test_subi_object.copy_animal('23949830', '0495823')

        # Make sure the copy is the same as the original
        original = test_subi_object.lookup_animal('23949830')[0]
        copy = test_subi_object.lookup_animal('0495823')[0]
        for key in original.keys():
            if key != 'animal_id' and original[key] != copy[key]:
                raise Exception("copy does not match original")

    def update_invalid_animal(self, test_subi_object):
        invalid_id = 'lkfjdkl'

        # Expect an exception
        try:
            test_subi_object.update_animal_field(invalid_id, 'bee', 2000)
            excepted = False
        except:
            excepted = True

        if excepted == False:
            raise Exception("Invalid animal id did not raise exception")

    def test_auto_increment(self, test_subi_object):
        # Append two new columns
        first_col_name = 'sldkfjkdl'
        second_col_name = 'glkwejwe'
        test_subi_object.create_col(first_col_name, 'BOOL', '')
        test_subi_object.create_col(second_col_name, 'BOOL', '')

        # Get info on the new colums
        first_order = test_subi_object.col_info(first_col_name)[0]['col_order']
        second_order = test_subi_object.col_info(second_col_name)[0]['col_order']

        # Clean up our mess
        test_subi_object.delete_col(first_col_name)
        test_subi_object.delete_col(second_col_name)

        # Test that the second column has a higher ordinal
        if (first_order >= second_order):
            raise Exception("First order, is not smaller than Second order")

    def test_unicode_support(self, test_subi_object):
        # Create a new column with a little unicode
        unicode_string = 'Феликс Дзержинский'
        test_subi_object.create_col('sdlfjdslkfd', 'BOOL', unicode_string)

        # Get the data back
        col_description = test_subi_object.col_info('sdlfjdslkfd')[0]['col_description']

        # Clean up our mess
        test_subi_object.delete_col('sdlfjdslkfd')

        if (col_description != unicode_string):
            raise Exception("Unicode not supported")

if __name__ == "__main__":
    #   this deletes the db!
    #   it should only be used during development
    test_subi_object = subi_db_class()
    test_subi_object.drop_tables()

    #   Run some integration tests
    print "Running integration tests..."
    test_object = subi_db_integration_test()
    test_subi_object = subi_db_class()

    test_object.non_unique_insert(test_subi_object)
    test_object.animal_update_and_lookup(test_subi_object)
    test_object.delete_animal(test_subi_object)

    test_object.add_columns(test_subi_object)
    test_object.add_duplicate_column_fails(test_subi_object)
    test_object.update_column(test_subi_object)
    test_object.delete_column(test_subi_object)

    test_object.regular_use_pattern(test_subi_object)

    # These are dependent on the db structure
    # established above.  Add new tests farther
    # down.
    # bmh Jan 2011
    test_object.get_unique_col_values(test_subi_object)
    test_object.search_fulltext(test_subi_object)
    test_object.dump_and_restore(test_subi_object)
    test_object.animal_exists(test_subi_object)
    test_object.copy_animal(test_subi_object)
    test_object.update_invalid_animal(test_subi_object)
    test_object.test_auto_increment(test_subi_object)
    test_object.test_unicode_support(test_subi_object)

    #   this deletes the db!
    #   it should only be used during development
    test_subi_object.drop_tables()

    print "Tests passed!"
    test_subi_object.close()


