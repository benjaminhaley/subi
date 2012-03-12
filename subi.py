#!/usr/bin/python
# -*- coding: utf-8 -*-

# Controller for subi webservice
#
# adapted from
#   Jon Berg , turtlemeat.com
#   http://fragments.turtlemeat.com/pythonwebserver.php
#
# by
#   Ben Haley - Dec 2011
#   <benjamin.haley@gmail.com>

from __future__ import unicode_literals
import string
import cgi
import time
from os import curdir, sep, path, listdir, unlink
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import urlparse, parse_qs
from scripts import subi_db
import json
import webbrowser
import codecs
import traceback
import re
import ast

# Configuration
webdir = 'web'
home_url = 'http://localhost/subi'
translations_file = 'language.txt'
delimiter = ";"


class MyHandler(BaseHTTPRequestHandler):

    def __authorize(self):
        """ Before anything else, always check that they are
            an authorized client.
        """
        authorized_clients = \
            [
                '127.0.0.1',     # localhost
                '127.0.0.1/8',   # localhost alias
                '127.0.0.1/8',   # localhost alias
                '::1',           # localhost in ipv6
                '::1/128'        # localhost alias in ipv6
            ]

        client = self.client_address[0]

        if not client in authorized_clients:
            raise Exception("Client is not authorized!")
            
    def __preprocess(self, html, language):
        """ To support multiple languages,
            all pages will be preprocessed.
            
            {{some text}} will be replaced using the translation file
        """
        replace = codecs.open(translations_file, 'r', 'utf-8-sig').read()
        replace = ast.literal_eval(replace)
        p = re.compile(r'\{\{.*?\}\}')
        
        # I have to compensate for this buggy bullshit
        # where the ast.literal_eval function converts everything
        # back to the original utf8 encoding, plus I need utf8 returned
        # at the end of the day
        html = p.sub(lambda m: 
            replace[m.group().encode('utf8')][language.encode('utf8')] 
            if m.group() in replace
            and language in replace[m.group()]
            else m.group()
            , html)
        
        return html

    def do_GET(self):

        # Security first
        self.__authorize()

        print ""
        print("Requested " + self.path)
        req = urlparse(self.path)
        q = parse_qs(req.query)
        
        try:
            # serve static content as is
            if req.path in [
                    "/jquery-1.7.1.min.js",
                    "/jquery-ui-1.8.16.min.js",
                    "/jquery.jeditable.mini.js",
                    "/jquery.form.js",
                    "/jquery-ui-1.8.css",
                    "/bootstrap.min.css",
                    "/bootstrap-dropdown.js",
                    "/favicon.ico"]:
                fpath = req.path

            # Handle erroneous requests
            elif req.path.endswith("/404"):
                fpath = "/404.html"

            # return the front page
            elif req.path == "/subi":
                fpath = "/subi.html"

            # handle data requests
            elif req.path == "/subi/ajax":
                self.do_AJAX()
                return

            # Give a csv from full text search
            # TODO move this with other full text search
            # into a non-redundant space
            elif req.path == "/subi/csv":
                self.__generate_temp_csv()

                # Send the file as a response
                self.__serve_file(
                    filename     = 'subi_results.csv', 
                    contents     = open('temp.csv').read(),
                    content_type = 'application/octet-stream'
                )

                return

            # Give a backup
            elif req.path == "/subi/backup":

                # make a new backup
                db = subi_db.subi_db_class()
                filename = db.backup_db()

                # open the backup file
                filepath = path.join('data', filename)

                # Send the file as a response
                self.__serve_file(
                    filename     = filename, 
                    contents     = open(filepath, 'r').read(),
                    content_type = 'application/octet-stream'
                )

                return


            # contents of the data folder should be accessible
            elif req.path == "/subi/data":

                # Determine the request
                requestfile = q['filename'][0]

                if requestfile not in listdir('data'):
                    # Make sure the requested file in in the data directory
                    self.__serve_404()
                    return

                else:
                    # Return the requested file
                    filepath = path.join('data', q['filename'][0])
                    self.__serve_file(
                        filename     = q['filename'][0], 
                        contents     = open(filepath).read(),
                        content_type = 'application/octet-stream'
                    )
                    return
                    
            # And they might want an offline manual
            elif req.path == "/subi/userguide.pdf":
                self.__serve_file(
                    filename     = 'userguide.pdf', 
                    contents     = open('userguide.pdf', 'rb').read(),
                    content_type = 'application/pdf'
                )
                return

            # if the request is not recognized return an error
            else:
                self.__serve_404()
                return

            # by default we return the corresponding file
            # in the web directory
            contents = open(webdir + fpath).read()

            # Determine the content type
            if fpath.endswith(".css"):
                content_type = 'text/css'
            elif fpath.endswith(".js"):
                content_type = 'application/javascript'
            else:
                content_type = 'text/html'
                # Preprocessing {{text_to_translate}} first
                if 'language' not in q:
                    q['language'] = ['english']
                contents = self.__preprocess(contents, q['language'][0])

            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(contents)
            return

        except IOError:
            self.__serve_404()
            
    def __serve_file(self, filename, contents, content_type):
        """ 
            Serve a file via http
        """
        self.send_response(200)
        self.send_header(
            'Content-disposition',
            'attachment; filename=%s' % filename)
        self.send_header('Content-type', content_type)
        self.end_headers()
        self.wfile.write(contents)
        return
       
    def __serve_404(self):
        """ 
            Let them know we are having trouble processing the request
        """
        self.send_error(
            404,
            'File Not Found: %s.  Please visit %s '% (self.path, home_url)
        )

        return
        
    def do_AJAX(self):
        """
            This is outside the specification of the class.
            It will handle any ajax query with a json response.
            Errors will be noted in json.
        """

        # Security first
        # (though this should have been handled in get or post)
        self.__authorize()

        req = urlparse(self.path)
        q = parse_qs(req.query)

        # Convert query to unicode
        for key, value in q.items():
            q[key][0] = value[0].decode('UTF-8')

        # A helper for developers
        print("Query contains: ")
        for key, value in q.items():
            print("    " + str(key) + ": " + str(value))

        db = subi_db.subi_db_class()

        # Determine command
        if 'command' not in q:
            response = {'error': 'No command in query, ' + self.path}
        else:
            command = q['command'][0]

        # Response is innocent until proven guilty
        response = {}
        response['ok'] = True

        # Execute command
        try:
            if command == "NO COMMAND SENT":
                pass

            elif command == "create_col":
                if 'col_group' not in q:
                    q['col_group'] = [None]
                db.create_col(
                    q['col_name'][0],
                    q['col_type'][0],
                    q['col_desc'][0],
                    q['col_group'][0]
                )

            elif command == "update_col":
                if 'field_value' not in q:
                    q['field_value'] = [None]
                db.update_col(
                    q['col_name'][0],
                    q['field_name'][0],
                    q['field_value'][0]
                )

            elif command == "delete_col":
                db.delete_col(q['col_name'][0])

            elif command == "insert_new_animal":
                print q['animal_id'][0]
                db.insert_new_animal(q['animal_id'][0])

            elif command == "update_animal_field":
                if 'col_value' not in q:
                    q['col_value'] = [None]

                db.update_animal_field(
                        q['animal_id'][0],
                        q['col_name'][0],
                        q['col_value'][0]
                        )

            elif command == "lookup_animal":
                data = db.lookup_animal(q['animal_id'][0])
                response['data'] = data

            elif command == "copy_animal":
                db.copy_animal(q['origin_id'][0], q['copy_id'][0])

            elif command == "animal_exists":
                data = db.animal_exists(q['animal_id'][0])
                response['data'] = data

            elif command == "delete_animal":
                db.delete_animal(q['animal_id'][0])

            elif command == "search_fulltext":
                # Fill in default values
                if 'limit' not in q:
                    q['limit'] = [10]
                if 'offset' not in q:
                    q['offset'] = [0]
                if 'search_terms' not in q:
                    q['search_terms'] = []
                else:
                    # Break search terms by spaces
                    # while preserving quoted strings
                    # We aren't using shlex, b.c. it doesn't have
                    # unicode support.  It should in the future, we
                    # will download it then.
                    q['search_terms'] = q['search_terms'][0].split(' ')

                result = db.search_fulltext(
                        q['search_terms'],
                        q['offset'][0],
                        q['limit'][0],
                        )

                # Template the response
                response['data'] = {}
                response['data']['animals'] = []
                response['data']['count'] = None

                for animal in result['animals']:
                    a = {}
                    for key in animal.keys():
                        a[key] = animal[key]
                    response['data']['animals'].append(a)

                response['data']['count'] = result['count']

            elif command == "col_info":
                data = db.col_info()
                response['data'] = []

                for column in data:
                    d = {}
                    for key in column.keys():
                        d[key] = column[key]
                    response['data'].append(d)

            elif command == "get_unique_col_values":
                if 'min_freq' not in q:
                    q['min_freq'] = [1]
                col_values = db.get_unique_col_values(
                                q['col_name'][0],
                                q['min_freq'][0]
                                )
                response['data'] = col_values

            elif command == "backup_db":
                data = db.backup_db()
                response['data'] = data

            elif command == "delete_backup":
                db.delete_backup(q['filename'][0])

            elif command == "list_backups":
                data = db.list_backups()
                response['data'] = data

            elif command == "load_db":
                db.load_db(q['filename'][0])

            else:
                response = {
                        'ok': False,
                        'error': 'Unrecognized command, ' + command
                        }

        except Exception as e:
            # add call and traceback info to error message so I can debug
            msg = "Requested " + self.path + "\n"
            msg += traceback.format_exc()
            response = {'ok': False, 'error': msg}

        # Tell them we have a good response with json
        # safari coughs if this is not here
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        # Send back some json
        json_response = json.dumps(response)
        self.wfile.write(json_response)
        return

        # db.create_col(col_name, col_type, col_desc, col_group)

    def do_POST(self):

        # Security first
        self.__authorize()
        
        # Open a connection to the
        db = subi_db.subi_db_class()

        global rootnode
        try:
            # Get the file from the post
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                query = cgi.parse_multipart(self.rfile, pdict)
            upfilecontent = query.get('filename')

            # First save it to the data dir
            filename = 'subi_backup_uploaded'
            filepath = path.join('data', filename)
            f = open(filepath, 'w')
            f.write(upfilecontent[0])
            f.close()
            
            # then instantiate it
            db.load_db(filename)

            # Send the filename back
            response = {'ok': True}

        except Exception as e:
            # add call and traceback info to error message so I can debug
            msg = "Requested " + self.path + "\n"
            msg += traceback.format_exc()
            response = {'ok': False, 'error': msg}

        json_response = json.dumps(response)
        self.send_response(200)
        #self.send_header('Content-type', 'application/json')
        self.end_headers()
        #self.wfile.write(json_response)
        return
        
    # make temp csv from the full text search
    # TODO move this with other full text search
    # into a non-redundant space
    def __generate_temp_csv(self):

        req = urlparse(self.path)
        q = parse_qs(req.query)
    
        # Open a connection to the
        db = subi_db.subi_db_class()

        # Fill in default values
        if 'limit' not in q:
            q['limit'] = [10000]
        if 'offset' not in q:
            q['offset'] = [0]
        if 'search_terms' not in q:
            q['search_terms'] = []
        else:
            # Break search terms by spaces
            # TODO preserve quoted strings
            q['search_terms'] = q['search_terms'][0].split(' ')

        # Request the column info for descriptions
        col_info = db.col_info()
        col_descriptions = []
        col_names = []
        for col in col_info:
            # Remove animal id because its used internally
            # and doesn't make sense to the user
            if(col['col_name'] != 'animal_id'):
                col_names.append(col['col_name'])
                col_descriptions.append(col['col_description'])

        # Request the animals
        result = db.search_fulltext(
                        q['search_terms'],
                        q['offset'][0],
                        q['limit'][0],
                        )

        # Start a csv file
        # We have to jump through some hoops
        # so that excel will recognize our csv, actually tsv.
        # We can't use the built in csv module, b.c. it does 
        # not provide unicode support.
        #
        # Mostly we need to:
        #   Use UTF 16 little endian
        #   use tab seperation
        #   Supply a BOM at teh begining of file to indicate endiness
        #
        # see 
        #   http://stackoverflow.com/questions/451636/whats-the-best-way-to-export-utf8-data-into-excel
        
        f = codecs.open('temp.csv', encoding='utf-16-le', mode='w')
        
        # Write the BOM to let them know its unicode
        f.write('\ufeff')
        
        # Write out the column headers
        header = ''
        for description in col_descriptions:
            # remove dangerous csv chars
            description = str(description).replace(delimiter, '')
            header += description + delimiter
        
        header += '\n'
        f.write(header)

        # Then the animals
        for animal in result['animals']:
            row = ''
            for name in col_names:
                value = unicode(animal[name])
                # remove csv dangerous chars
                value = value.replace(delimiter, '')
                row += value + delimiter

            # Finish the line
            row += '\n'
            f.write(row)
        
        f.close()


def main():
    try:
        # Start the server
        server = HTTPServer(('', 8000), MyHandler)
        print 'started httpserver...'

        # Open the subi webpage
        url = 'http://localhost:8000/subi'
        webbrowser.open_new(url)

        # Don't stop serving
        server.serve_forever()

    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()

if __name__ == '__main__':
    main()

