#!/usr/bin/python
# -*- coding: utf-8 -*-


class subi_db_class:
    connection = None
    acceptable_col_types = ['VARCHAR(120)','DECIMAL(10,10)','BOOL']

    #   basic functions
    def __init__(self):
        import sqlite3 as lite
        import sys
        self.connection = lite.connect('subi.db')
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
                          (animal_id varchar(12));
                          """)
        connection.commit()
        cursor.execute("""CREATE TABLE col_definitions 
                          (col_name varchar(12),
                           col_description varchar(12),
                           col_type varchar(12),
                           col_order integer(3),
                           col_group varchar(12),
                           active bool);
                          """)
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
                          FROM   col_definitions;
                          """)
        rows = cursor.fetchall()
        for row in rows:
            col_names.append(row['col_name'])
        return col_names
        

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

    
    def __generate_new_col_name(self):
        import string
        import random

        chars = string.ascii_letters
        col_name = ''.join(random.choice(chars) for x in range(6))
        while self.__col_exists(col_name):
            col_name = self.__generate_new_col_name()
        return col_name
        

    def __validate_col_type(self, col_type):
        if col_type not in self.acceptable_col_types:
            raise Exception('col_type must fit one of acceptable data types.')      

    def col_info(self, col_name = None):
        #   Returns a list of dictionary row objects
        #   If col_name is passed in, only definitions for that column are returned
        #   otherwise, all are returned
        import sqlite3 as lite

        sql_str = ''
        if col_name == None:
            pass
        else:
            sql_str_list = "AND col_name ='" , col_name , "'"
            sql_str = "".join(sql_str_list)
        
        connection = self.connection
        connection.row_factory = lite.Row
        cursor = connection.cursor() 
        cursor.execute("""SELECT *
                          FROM   col_definitions
                          WHERE  active = 1
                          %s;
                          """ %sql_str)
        rows = cursor.fetchall()
        return rows

    def create_col(self, col_type, col_desc, col_group = None):
        #   column names are managed in col_defininitions because sqlite can't rename columns:
        #   http://stackoverflow.com/questions/805363/how-do-i-rename-a-column-in-a-sqlite-database-table

        self.__validate_col_type(col_type)
        connection = self.connection

        col_name = self.__generate_new_col_name()
        sql_args = col_name, col_desc, col_type, col_group
        cursor = connection.cursor()
        cursor.execute("""  INSERT INTO col_definitions
                            (col_name, col_description, col_type, col_group, active)
                            VALUES
                            ('%s', '%s', '%s', '%s', 1);""" % sql_args)
        connection.commit()

        #   add columnn to animals table
        sql_args = col_name, col_type
        cursor = connection.cursor()
        cursor.execute(""" ALTER TABLE animals ADD %s %s;""" % sql_args)
        connection.commit()

        return col_name
    

    def update_col(self, col_name, col_type, col_desc, col_group = None):
        self.__validate_col_type(col_type)
 
        connection = self.connection

        #   update column in column_definitions table
        sql_args = col_desc, col_type, col_group, col_name
        cursor = connection.cursor()
        cursor.execute("""  UPDATE  col_definitions
                            SET     col_description = '%s'
                            ,       col_type = '%s'
                            ,       col_group = '%s'
                            WHERE   col_name = '%s';""" % sql_args)
        connection.commit()

    def delete_col(self, col_name):
        connection = self.connection
        cursor = connection.cursor()
        cursor.execute("""  UPDATE  col_definitions
                            SET     active = 0
                            WHERE   col_name = '%s';""" % col_name)
        connection.commit()


    #   animal functions
    def insert_new_animal(self, animal_id):
        if self.lookup_animal(animal_id) != None:
            raise Exception("Animal id already in database")
        connection = self.connection
        cursor = connection.cursor()
        cursor.execute(""" INSERT INTO animals (animal_id)
                           VALUES ('%s');
                          """ % animal_id)
        connection.commit()

    
    def update_animal_field(self, animal_id, col_name, col_value):
        connection = self.connection
        cursor = connection.cursor()
        sql_args = col_name, col_value, animal_id
        cursor.execute(""" UPDATE animals
                           SET    %s = '%s'
                           WHERE  animal_id = '%s';
                           """ % sql_args)
        connection.commit()       

    def delete_animal(self, animal_id):
        connection = self.connection
        cursor = connection.cursor()
        cursor.execute(""" DELETE FROM animals
                           WHERE  animal_id = '%s';
                           """ % animal_id)
        connection.commit() 


    def lookup_animal(self, animal_id):
        import sqlite3 as lite
        connection = self.connection

        #   this will allow the data to get returned as a dictionary
        connection.row_factory = lite.Row
        cursor = connection.cursor() 
        cursor.execute("""SELECT *
                          FROM   animals
                          WHERE  animal_id = '%s';
                          """ % animal_id)
        rows = cursor.fetchall()
        if len(rows) > 1:
            raise Exception("More than one matching animal_id was found. They should be unique.")
        elif len(rows) == 0:
            animal_dict = None
        else:
            animal_dict = rows[0]
        return animal_dict


    #   return a set of lists with all of the active (non-deleted) animal data
    def all_animals(self):
        

    #   functions to be used for testing only
    def drop_tables(self):
        connection = self.connection
        cursor = connection.cursor()       
        cursor.execute("""DROP TABLE animals;""")
        connection.commit()
        cursor.execute("""DROP TABLE col_definitions;""")
        connection.commit()

    


class subi_db_integration_test:
    def non_unique_insert(self, subi_db_object):
        import random
        rand_id = random.randint(100000000,99999999999)
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
        rand_id = unicode(random.randint(100000000,99999999999))
        subi_db_object.insert_new_animal(rand_id)
        looked_up_row = subi_db_object.lookup_animal(rand_id)
        if looked_up_row["animal_id"] != rand_id:
            raise Exception('Insert animal test failed.')

        #   create a column, then update the value for the inserted animal
        turtle_col_name = subi_db_object.create_col('DECIMAL(10,10)','this column is about turtles')
        subi_db_object.update_animal_field(rand_id,turtle_col_name,2000)
        looked_up_row = subi_db_object.lookup_animal(rand_id)
        if looked_up_row[turtle_col_name] != 2000:
            raise Exception('Update animal field test failed.')

    def delete_animal(self, subi_db_object):
        import random
        
        rand_id = unicode(random.randint(100000000,99999999999))
        subi_db_object.insert_new_animal(rand_id)
        subi_db_object.delete_animal(rand_id)
        looked_up_row = subi_db_object.lookup_animal(rand_id)
        if looked_up_row != None:
            raise Exception('Delete animal test failed.')

    def add_columns(self, subi_db_object):
        col_type = 'BOOL'
        col_desc = 'Some boolean column'
        col_group = 'boolean items'
        col_name = subi_db_object.create_col(col_type, col_desc, col_group)
        col_info = subi_db_object.col_info(col_name)
        for row in col_info:
            if row['col_type'] != col_type:
                raise Exception('col_type did not match')
            if row['col_description'] != col_desc:
                raise Exception('col_desc did not match')

    def update_column(self, subi_db_object):
        col_type = 'BOOL'
        col_desc = 'Some boolean column'
        col_group = 'boolean items'
        col_name = subi_db_object.create_col(col_type, col_desc, col_group)

        col_type = 'BOOL'
        col_desc = 'New column description'
        col_group = 'new group'
        subi_db_object.update_col(col_name, col_type, col_desc, col_group = None)
        col_info = subi_db_object.col_info(col_name)
        for row in col_info:
            if row['col_type'] != col_type:
                raise Exception('col_type did not match')
            if row['col_description'] != col_desc:
                raise Exception('col_desc did not match')        

    def delete_column(self, subi_db_object):
        col_type = 'BOOL'
        col_desc = 'Some boolean column'
        col_group = 'boolean items'
        col_name = subi_db_object.create_col(col_type, col_desc, col_group)
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
        col_type = 'BOOL'
        col_desc = 'Some boolean column'
        col_group = 'boolean items'
        #   the column name gets returned
        col_name = subi_db_object.create_col(col_type, col_desc, col_group)

        #   update the column to be in a different group
        col_type = 'BOOL'
        col_desc = 'Some boolean column'
        col_group = 'new group name'
        subi_db_object.update_col(col_name, col_type, col_desc, col_group)
       
        #   create a new animal
        import random
        rand_id = unicode(random.randint(100000000, 99999999999))
        subi_db_object.insert_new_animal(rand_id)

        #   update the animals' value for colname
        subi_db_object.update_animal_field(rand_id, col_name, 2000)

        #   look up the animal
        looked_up_row = subi_db_object.lookup_animal(rand_id)

        #   delete the animal
        subi_db_object.delete_animal(rand_id)

        #   delete the column
        subi_db_object.delete_col(col_name)

        #   here, you would close the connection
        #   subi_db_object.close()
        

if __name__ == "__main__":
    #   Run some integration tests
    print "Running integration tests..."
    test_object = subi_db_integration_test()
    test_subi_object = subi_db_class()

    test_object.non_unique_insert(test_subi_object)
    test_object.animal_update_and_lookup(test_subi_object)
    test_object.delete_animal(test_subi_object)
    
    test_object.add_columns(test_subi_object)
    test_object.update_column(test_subi_object)
    test_object.delete_column(test_subi_object)

    test_object.regular_use_pattern(test_subi_object)

    print "Tests passed!"
    test_subi_object.close()





