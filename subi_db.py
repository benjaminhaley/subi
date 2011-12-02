#!/usr/bin/python
# -*- coding: utf-8 -*-


class subi_db:
    connection = None

    def __init__(self):
        import sqlite3 as lite
        import sys
        self.connection = lite.connect('subi.db')
        if self.tables_exist() == False:
            self.create_tables()

    def close(self):
        self.connection.close()
    
    def tables_exist(self):
        connection = self.connection
        cursor = connection.cursor()
        TABLES_EXISTS = False
        
        cursor.execute("""SELECT name
                          FROM   sqlite_master
                          WHERE  (name = 'animals' OR name = 'col_definitions')
                          AND    type = 'table';
                          """)
        rows = cursor.fetchall()
        if len(rows) == 2:
            TABLES_EXISTS = True
        else:
            TABLES_EXISTS = False
        return TABLES_EXISTS


    def create_tables(self):
        connection = self.connection
        cursor = connection.cursor()       
        cursor.execute("""CREATE TABLE animals 
                          (animal_id varchar(12));
                          """)
        connection.commit()
        cursor.execute("""CREATE TABLE col_definitions 
                          (animal_id varchar(12));
                          """)
        connection.commit()
        print "Creating animals table"


    #   this is for testing purposes only
    def drop_tables(self):
        connection = self.connection
        cursor = connection.cursor()       
        cursor.execute("""DROP TABLE animals;""")
        connection.commit()
        cursor.execute("""DROP TABLE col_definitions;""")
        connection.commit()
        

    def column_list(self):
        col_list = list()
        
        connection = self.connection
        cursor = connection.cursor()       
        cursor.execute("""pragma table_info(animals);""")
        rows = cursor.fetchall()
        for row in rows:
            col_list.append(row[1])
        return col_list
     

    def insert_new_animal(self, animal_id):
        connection = self.connection
        cursor = connection.cursor()
        cursor.execute(""" INSERT INTO animals (animal_id)
                           VALUES ('%s');
                          """ % animal_id)
        connection.commit()
    

    def create_col(self, col_name, col_type):
        acceptable_cols = ['VARCHAR(12)','VARCHAR(50)','REAL','INTEGER']
        if col_type not in acceptable_cols:
            raise Exception('col_type must fit one of acceptable data types.')

        sql_args = col_name, col_type

        connection = self.connection
        cursor = connection.cursor()
        cursor.execute(""" ALTER TABLE animals ADD %s %s;""" % sql_args)
        connection.commit()



subi_db = subi_db()

#   insert some test data
subi_db.insert_new_animal('23')
subi_db.create_col('turle','REAL')
subi_db.drop_tables()
subi_db.close()


