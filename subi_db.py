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
                           col_group varchar(12));
                          """)
        connection.commit()


    #   column functions
    def __column_names(self):
        col_list = list()
        
        connection = self.connection
        cursor = connection.cursor()       
        cursor.execute("""pragma table_info(animals);""")
        rows = cursor.fetchall()
        for row in rows:
            col_list.append(row[1])
        return col_list


    def __column_types(self):
        col_list = list()
        
        connection = self.connection
        cursor = connection.cursor()       
        cursor.execute("""pragma table_info(animals);""")
        rows = cursor.fetchall()
        for row in rows:
            col_list.append(row[2])
        return col_list    

    
    def __validate_col_name(self, col_name):
        #   only allow letters and underscores
        col_name = col_name.replace("_","")
        IS_VALID = col_name.isalpha()
        if not IS_VALID:
            raise Exception("Column names can be letters or underscores, %s was passed in." % col_name)

    def __validate_col_type(self, col_type):
        if col_type not in self.acceptable_col_types:
            raise Exception('col_type must fit one of acceptable data types.')      

    def create_col(self, col_name, col_type, col_desc, col_group = None):
        self.__validate_col_type(col_type)
        self.__validate_col_name(col_name)
 
        connection = self.connection

        #   add columnn to animals table
        sql_args = col_name, col_type
        cursor = connection.cursor()
        cursor.execute(""" ALTER TABLE animals ADD %s %s;""" % sql_args)
        connection.commit()

        #   add column to column_definitions table
        sql_args = col_name, col_desc, col_type, col_group
        cursor = connection.cursor()
        cursor.execute("""  INSERT INTO col_definitions
                            (col_name, col_description, col_type, col_group)
                            VALUES
                            ('%s', '%s', '%s', '%s');""" % sql_args)
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


    #   functions to be used for testing only
    def drop_tables(self):
        connection = self.connection
        cursor = connection.cursor()       
        cursor.execute("""DROP TABLE animals;""")
        connection.commit()
        cursor.execute("""DROP TABLE col_definitions;""")
        connection.commit()
        


class subi_db_unit_test:
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
        subi_db_object.create_col('turtle','DECIMAL(10,10)','this column is about turtles')
        subi_db_object.update_animal_field(rand_id,'turtle',2000)
        looked_up_row = subi_db_object.lookup_animal(rand_id)
        if looked_up_row["turtle"] != 2000:
            raise Exception('Update animal field test failed.')

    def add_columns(self, subi_db_object):
        #   I need to add column tests here
        pass


subi_db = subi_db_class()
subi_db.drop_tables()
subi_db = subi_db_class()

#   informal tests 
subi_db.insert_new_animal('24')
subi_db.insert_new_animal('dog')
subi_db.create_col('turtle','DECIMAL(10,10)', 'This col is about turtles')
subi_db.create_col('string_col','VARCHAR(120)', 'A very sexy string col')

subi_db.update_animal_field('24','turtle',2000)
subi_db.drop_tables()


#   Run some integration tests
print "Running integration tests..."
test_object = subi_db_unit_test()
test_subi_object = subi_db_class()
print "Tests passed!"

test_object.non_unique_insert(test_subi_object)
test_object.animal_update_and_lookup(test_subi_object)
test_subi_object.close()





