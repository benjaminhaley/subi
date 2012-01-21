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
from os import curdir, sep, path, listdir
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import urlparse, parse_qs
from scripts import subi_db
import json
import shlex          # "'a very' nice boy" -> ['a very', nice, boy]
import json

webdir = 'web'
home_url = 'http://localhost/subi'


class MyHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        print ""
        print("Requested " + self.path)
        req = urlparse(self.path)
        try:
            # serve static content as is
            if req.path in [
                    "/jquery-1.7.1.min.js",
                    "/jquery-ui-1.8.16.min.js",
                    "/jquery.jeditable.mini.js",
                    "/jquery-ui-1.8.css",
                    "/bootstrap.min.css",
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

            # contents of the data folder should be accessible
            elif req.path == "/subi/data":

                # Determine the request
                req = urlparse(self.path)
                q = parse_qs(req.query)
                requestfile = q['filename'][0]

                if requestfile not in listdir('data'):
                    # Make sure the requested file in in the data directory
                    self.send_response(301)
                    self.send_header('Location', '404')
                    self.end_headers()
                    return

                else:
                    # Return the requested file
                    filepath = path.join('data', q['filename'][0])
                    f = open(filepath)
                    self.send_response(200)
                    self.send_header(
                        'Content-disposition',
                        'attachment; filename=%s' % q['filename'][0])
                    self.send_header('Content-type', 'application/sdb')
                    self.end_headers()
                    self.wfile.write(f.read())
                    f.close()
                    return

            # if the request is not recognized return an error
            else:
                self.send_response(301)
                self.send_header('Location', '404')
                self.end_headers()
                return

            # by default we return the corresponding .html file
            # in the web directory
            f = open(webdir + fpath)
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
            return

        except IOError:
            self.send_error(
                404,
                'File Not Found: %s.  Please visit %s '
                 % (self.path, home_url)
            )

    def do_AJAX(self):
        """
            This is outside the specification of the class.
            It will handle any ajax query with a json response.
            Errors will be noted in json.
        """
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
                    q['search_terms'] = shlex.split(q['search_terms'][0])

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

            elif command == "load_db":
                data = db.load_db(q['filename'][0])
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
#           raise
            import traceback
            # add call and traceback info to error message so I can debug
            msg = "Requested " + self.path + "\n"
            msg += traceback.format_exc()
            response = {'ok': False, 'error': msg}

#        print("Animals table: ")
#        rows = db.run_sql_query("SELECT * FROM animals")
#        if len(rows) > 0:
#            print("    " + str(rows[0].keys()))
#        for row in rows:
#            print "    ",
#            print row
#        print("Column definitions ")
#        rows = db.run_sql_query("SELECT * FROM col_definitions")
#        if len(rows) > 0:
#            print("    " + str(rows[0].keys()))
#        for row in rows:
#            print "    ",
#            print row

        # Send back some json
        json_response = json.dumps(response)
        self.wfile.write(json_response)
        return

        # db.create_col(col_name, col_type, col_desc, col_group)

    def do_POST(self):
        global rootnode
        try:
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                query = cgi.parse_multipart(self.rfile, pdict)
            self.send_response(301)

            self.end_headers()
            upfilecontent = query.get('upfile')
            print "filecontent", upfilecontent[0]
            self.wfile.write("<HTML>POST OK.<BR><BR>")
            self.wfile.write(upfilecontent[0])

        except:
            pass


def main():
    try:
        server = HTTPServer(('', 80), MyHandler)
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()

if __name__ == '__main__':
    main()

