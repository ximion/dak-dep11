#!/usr/bin/env python

# Debian Archive Kit Database Update Script
# Copyright (C) 2008  Michael Casadevall <mcasadevall@debian.org>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

################################################################################

# <Ganneff> when do you have it written?
# <NCommander> Ganneff, after you make my debian account
# <Ganneff> blackmail wont work
# <NCommander> damn it

################################################################################

import psycopg2, sys, fcntl, os
import apt_pkg
import time
from daklib import database
from daklib import utils

################################################################################

Cnf = None
projectB = None
required_database_schema = 1

################################################################################

class UpdateDB:
    def usage (self, exit_code=0):
        print """Usage: dak update-db
Updates dak's database schema to the lastest version. You should disable crontabs while this is running

  -h, --help                show this help and exit."""
        sys.exit(exit_code)


################################################################################

    def update_db_to_zero(self):
        # This function will attempt to update a pre-zero database schema to zero

        # First, do the sure thing, and create the configuration table
        try:
            print "Creating configuration table ..."
            c = self.db.cursor()
            c.execute("""CREATE TABLE config (
                                  id SERIAL PRIMARY KEY NOT NULL,
                                  name TEXT UNIQUE NOT NULL,
                                  value TEXT
                                );""")
            c.execute("INSERT INTO config VALUES ( nextval('config_id_seq'), 'db_revision', '0')");
            self.db.commit()

        except psycopg2.ProgrammingError:
            self.db.rollback()
            print "Failed to create configuration table."
            print "Can the projectB user CREATE TABLE?"
            print ""
            print "Aborting update."
            sys.exit(-255)

################################################################################

    def get_db_rev(self):
        global projectB

        # We keep database revision info the config table
        # Try and access it

        try:
            c = self.db.cursor()
            q = c.execute("SELECT value FROM config WHERE name = 'db_revision';");
            return c.fetchone()[0]

        except psycopg2.ProgrammingError:
            # Whoops .. no config table ...
            self.db.rollback()
            print "No configuration table found, assuming dak database revision to be pre-zero"
            return -1

################################################################################

    def update_db(self):
        # Ok, try and find the configuration table
        print "Determining dak database revision ..."

        try:
            self.db = psycopg2.connect("dbname='" + Cnf["DB::Name"] + "' host='" + Cnf["DB::Host"] + "' port='" + str(Cnf["DB::Port"]) + "'")

        except:
            print "FATAL: Failed connect to database"
            pass

        database_revision = int(self.get_db_rev())

        if database_revision == -1:
            print "dak database schema predates update-db."
            print ""
            print "This script will attempt to upgrade it to the lastest, but may fail."
            print "Please make sure you have a database backup handy. If you don't, press Ctrl-C now!"
            print ""
            print "Continuing in five seconds ..."
            time.sleep(5)
            print ""
            print "Attempting to upgrade pre-zero database to zero"

            self.update_db_to_zero()
            database_revision = 0

        print "dak database schema at " + str(database_revision)
        print "dak version requires schema " + str(required_database_schema)

        if database_revision == required_database_schema:
            print "no updates required"
            sys.exit(0)

        for i in range (database_revision, required_database_schema):
            print "updating databse schema from " + str(database_revision) + " to " + str(i+1)
            dakdb = __import__("dakdb", globals(), locals(), ['update'+str(i+1)])
            update_module = getattr(dakdb, "update"+str(i+1))
            update_module.do_update(self)
            database_revision += 1

################################################################################

    def init (self):
        global Cnf, projectB

        Cnf = utils.get_conf()
        arguments = [('h', "help", "Update-DB::Options::Help")]
        for i in [ "help" ]:
            if not Cnf.has_key("Update-DB::Options::%s" % (i)):
                Cnf["Update-DB::Options::%s" % (i)] = ""

        arguments = apt_pkg.ParseCommandLine(Cnf, arguments, sys.argv)

        options = Cnf.SubTree("Update-DB::Options")
        if options["Help"]:
            usage()
        elif arguments:
            utils.warn("dak update-db takes no arguments.")
            usage(exit_code=1)


        self.update_db()

        try:
            lock_fd = os.open(Cnf["Dinstall::LockFile"], os.O_RDWR | os.O_CREAT)
            fcntl.lockf(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError, e:
            if errno.errorcode[e.errno] == 'EACCES' or errno.errorcode[e.errno] == 'EAGAIN':
                utils.fubar("Couldn't obtain lock; assuming another 'dak process-unchecked' is already running.")


################################################################################

if __name__ == '__main__':
    app = UpdateDB()
    app.init()

def main():
    app = UpdateDB()
    app.init()