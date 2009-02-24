#!/usr/bin/env python

"""
Database Update Script - Fix bin_assoc_by_arch view

@contact: Debian FTP Master <ftpmaster@debian.org>
@copyright: 2009  Joerg Jaspert <joerg@debian.org>
@license: GNU General Public License version 2 or later

"""

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

import psycopg2
from daklib.dak_exceptions import DBUpdateError

################################################################################

def do_update(self):
    """ Execute the DB update """

    print "Fixing bin_assoc_by_arch view"
    try:
        c = self.db.cursor()
        c.execute("DROP VIEW bin_assoc_by_arch")

        c.execute("""CREATE OR REPLACE VIEW bin_assoc_by_arch AS
        SELECT ba.suite, ba.bin, a.id AS arch
        FROM bin_associations ba
        JOIN binaries b ON ba.bin = b.id, architecture a
        WHERE a.id > 2 AND (b.architecture = 2 OR b.architecture = a.id) """)
        c.execute("UPDATE config SET value = '5' WHERE name = 'db_revision'")

        self.db.commit()

    except psycopg2.ProgrammingError, msg:
        self.db.rollback()
        raise DBUpdateError, "Unable to recreate bin_assoc_by_arch view, rollback issued. Error message : %s" % (str(msg))