#!/usr/bin/env python

# DB access fucntions
# Copyright (C) 2000, 2001, 2002, 2003, 2004, 2006  James Troup <james@nocrew.org>

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

import sys
import time
import types

################################################################################

Cnf = None
projectB = None
suite_id_cache = {}
section_id_cache = {}
priority_id_cache = {}
override_type_id_cache = {}
architecture_id_cache = {}
archive_id_cache = {}
component_id_cache = {}
location_id_cache = {}
maintainer_id_cache = {}
keyring_id_cache = {}
source_id_cache = {}
files_id_cache = {}
maintainer_cache = {}
fingerprint_id_cache = {}
queue_id_cache = {}
uid_id_cache = {}
suite_version_cache = {}

################################################################################

def init (config, sql):
    """ database module init. Just sets two variables"""
    global Cnf, projectB

    Cnf = config
    projectB = sql


def do_query(q):
    """
    Executes a database query q. Writes statistics to stderr and returns
    the result.

    """
    sys.stderr.write("query: \"%s\" ... " % (q))
    before = time.time()
    r = projectB.query(q)
    time_diff = time.time()-before
    sys.stderr.write("took %.3f seconds.\n" % (time_diff))
    if type(r) is int:
        sys.stderr.write("int result: %s\n" % (r))
    elif type(r) is types.NoneType:
        sys.stderr.write("result: None\n")
    else:
        sys.stderr.write("pgresult: %s\n" % (r.getresult()))
    return r

################################################################################

def get_suite_id (suite):
    """ Returns database suite_id for given suite, caches result. """
    global suite_id_cache

    if suite_id_cache.has_key(suite):
        return suite_id_cache[suite]

    q = projectB.query("SELECT id FROM suite WHERE suite_name = '%s'" % (suite))
    ql = q.getresult()
    if not ql:
        return -1

    suite_id = ql[0][0]
    suite_id_cache[suite] = suite_id

    return suite_id

def get_section_id (section):
    """ Returns database section_id for given section, caches result. """
    global section_id_cache

    if section_id_cache.has_key(section):
        return section_id_cache[section]

    q = projectB.query("SELECT id FROM section WHERE section = '%s'" % (section))
    ql = q.getresult()
    if not ql:
        return -1

    section_id = ql[0][0]
    section_id_cache[section] = section_id

    return section_id

def get_priority_id (priority):
    """ Returns database priority_id for given priority, caches result. """
    global priority_id_cache

    if priority_id_cache.has_key(priority):
        return priority_id_cache[priority]

    q = projectB.query("SELECT id FROM priority WHERE priority = '%s'" % (priority))
    ql = q.getresult()
    if not ql:
        return -1

    priority_id = ql[0][0]
    priority_id_cache[priority] = priority_id

    return priority_id

def get_override_type_id (type):
    """ Returns database override_id for given override_type type, caches result. """
    global override_type_id_cache

    if override_type_id_cache.has_key(type):
        return override_type_id_cache[type]

    q = projectB.query("SELECT id FROM override_type WHERE type = '%s'" % (type))
    ql = q.getresult()
    if not ql:
        return -1

    override_type_id = ql[0][0]
    override_type_id_cache[type] = override_type_id

    return override_type_id

def get_architecture_id (architecture):
    """ Returns database architecture_id for given architecture, caches result. """
    global architecture_id_cache

    if architecture_id_cache.has_key(architecture):
        return architecture_id_cache[architecture]

    q = projectB.query("SELECT id FROM architecture WHERE arch_string = '%s'" % (architecture))
    ql = q.getresult()
    if not ql:
        return -1

    architecture_id = ql[0][0]
    architecture_id_cache[architecture] = architecture_id

    return architecture_id

def get_archive_id (archive):
    """ Returns database archive_id for given archive, caches result. """
    global archive_id_cache

    archive = archive.lower()

    if archive_id_cache.has_key(archive):
        return archive_id_cache[archive]

    q = projectB.query("SELECT id FROM archive WHERE lower(name) = '%s'" % (archive))
    ql = q.getresult()
    if not ql:
        return -1

    archive_id = ql[0][0]
    archive_id_cache[archive] = archive_id

    return archive_id

def get_component_id (component):
    """ Returns database component_id for given component, caches result. """
    global component_id_cache

    component = component.lower()

    if component_id_cache.has_key(component):
        return component_id_cache[component]

    q = projectB.query("SELECT id FROM component WHERE lower(name) = '%s'" % (component))
    ql = q.getresult()
    if not ql:
        return -1

    component_id = ql[0][0]
    component_id_cache[component] = component_id

    return component_id

def get_location_id (location, component, archive):
    """
    Returns database location_id for given combination of
    location
    component
    archive.

    The 3 parameters are the database ids returned by the respective
    "get_foo_id" functions.

    The result will be cached.

    """
    global location_id_cache

    cache_key = location + '_' + component + '_' + location
    if location_id_cache.has_key(cache_key):
        return location_id_cache[cache_key]

    archive_id = get_archive_id (archive)
    if component != "":
        component_id = get_component_id (component)
        if component_id != -1:
            q = projectB.query("SELECT id FROM location WHERE path = '%s' AND component = %d AND archive = %d" % (location, component_id, archive_id))
    else:
        q = projectB.query("SELECT id FROM location WHERE path = '%s' AND archive = %d" % (location, archive_id))
    ql = q.getresult()
    if not ql:
        return -1

    location_id = ql[0][0]
    location_id_cache[cache_key] = location_id

    return location_id

def get_source_id (source, version):
    """ Returns database source_id for given combination of source and version, caches result. """
    global source_id_cache

    cache_key = source + '_' + version + '_'
    if source_id_cache.has_key(cache_key):
        return source_id_cache[cache_key]

    q = projectB.query("SELECT id FROM source s WHERE s.source = '%s' AND s.version = '%s'" % (source, version))

    if not q.getresult():
        return None

    source_id = q.getresult()[0][0]
    source_id_cache[cache_key] = source_id

    return source_id

def get_suite_version(source, suite):
    """ Returns database version for a given source in a given suite, caches result. """
    global suite_version_cache
    cache_key = "%s_%s" % (source, suite)

    if suite_version_cache.has_key(cache_key):
        return suite_version_cache[cache_key]

    q = projectB.query("""
    SELECT s.version FROM source s, suite su, src_associations sa
    WHERE sa.source=s.id
      AND sa.suite=su.id
      AND su.suite_name='%s'
      AND s.source='%s'"""
                              % (suite, source))

    if not q.getresult():
        return None

    version = q.getresult()[0][0]
    suite_version_cache[cache_key] = version

    return version

################################################################################

def get_or_set_maintainer_id (maintainer):
    """
    If maintainer does not have an entry in the maintainer table yet, create one
    and return its id.
    If maintainer already has an entry, simply return its id.

    Result is cached.

    """
    global maintainer_id_cache

    if maintainer_id_cache.has_key(maintainer):
        return maintainer_id_cache[maintainer]

    q = projectB.query("SELECT id FROM maintainer WHERE name = '%s'" % (maintainer))
    if not q.getresult():
        projectB.query("INSERT INTO maintainer (name) VALUES ('%s')" % (maintainer))
        q = projectB.query("SELECT id FROM maintainer WHERE name = '%s'" % (maintainer))
    maintainer_id = q.getresult()[0][0]
    maintainer_id_cache[maintainer] = maintainer_id

    return maintainer_id

################################################################################

def get_or_set_keyring_id (keyring):
    """
    If keyring does not have an entry in the keyring table yet, create one
    and return its id.
    If keyring already has an entry, simply return its id.

    Result is cached.

    """
    global keyring_id_cache

    if keyring_id_cache.has_key(keyring):
        return keyring_id_cache[keyring]

    q = projectB.query("SELECT id FROM keyrings WHERE name = '%s'" % (keyring))
    if not q.getresult():
        projectB.query("INSERT INTO keyrings (name) VALUES ('%s')" % (keyring))
        q = projectB.query("SELECT id FROM keyrings WHERE name = '%s'" % (keyring))
    keyring_id = q.getresult()[0][0]
    keyring_id_cache[keyring] = keyring_id

    return keyring_id

################################################################################

def get_or_set_uid_id (uid):
    """
    If uid does not have an entry in the uid table yet, create one
    and return its id.
    If uid already has an entry, simply return its id.

    Result is cached.

    """
    global uid_id_cache

    if uid_id_cache.has_key(uid):
        return uid_id_cache[uid]

    q = projectB.query("SELECT id FROM uid WHERE uid = '%s'" % (uid))
    if not q.getresult():
        projectB.query("INSERT INTO uid (uid) VALUES ('%s')" % (uid))
        q = projectB.query("SELECT id FROM uid WHERE uid = '%s'" % (uid))
    uid_id = q.getresult()[0][0]
    uid_id_cache[uid] = uid_id

    return uid_id

################################################################################

def get_or_set_fingerprint_id (fingerprint):
    """
    If fingerprintd does not have an entry in the fingerprint table yet, create one
    and return its id.
    If fingerprint already has an entry, simply return its id.

    Result is cached.

    """
    global fingerprint_id_cache

    if fingerprint_id_cache.has_key(fingerprint):
        return fingerprint_id_cache[fingerprint]

    q = projectB.query("SELECT id FROM fingerprint WHERE fingerprint = '%s'" % (fingerprint))
    if not q.getresult():
        projectB.query("INSERT INTO fingerprint (fingerprint) VALUES ('%s')" % (fingerprint))
        q = projectB.query("SELECT id FROM fingerprint WHERE fingerprint = '%s'" % (fingerprint))
    fingerprint_id = q.getresult()[0][0]
    fingerprint_id_cache[fingerprint] = fingerprint_id

    return fingerprint_id

################################################################################

def get_files_id (filename, size, md5sum, location_id):
    """
    Returns -1, -2 or the file_id for a given combination of
    filename
    size
    md5sum
    location_id.

    The database is queried using filename and location_id, size and md5sum are for
    extra checks.

    Return values:
    -1 - The given combination of arguments result in more (or less) than
         one result from the database
    -2 - The given size and md5sum do not match the values in the database
    anything else is a file_id

    Result is cached.

    """
    global files_id_cache

    cache_key = "%s_%d" % (filename, location_id)

    if files_id_cache.has_key(cache_key):
        return files_id_cache[cache_key]

    size = int(size)
    q = projectB.query("SELECT id, size, md5sum FROM files WHERE filename = '%s' AND location = %d" % (filename, location_id))
    ql = q.getresult()
    if ql:
        if len(ql) != 1:
            return -1
        ql = ql[0]
        orig_size = int(ql[1])
        orig_md5sum = ql[2]
        if orig_size != size or orig_md5sum != md5sum:
            return -2
        files_id_cache[cache_key] = ql[0]
        return files_id_cache[cache_key]
    else:
        return None

################################################################################

def get_or_set_queue_id (queue):
    """
    If queue does not have an entry in the queue_name table yet, create one
    and return its id.
    If queue already has an entry, simply return its id.

    Result is cached.

    """
    global queue_id_cache

    if queue_id_cache.has_key(queue):
        return queue_id_cache[queue]

    q = projectB.query("SELECT id FROM queue WHERE queue_name = '%s'" % (queue))
    if not q.getresult():
        projectB.query("INSERT INTO queue (queue_name) VALUES ('%s')" % (queue))
        q = projectB.query("SELECT id FROM queue WHERE queue_name = '%s'" % (queue))
    queue_id = q.getresult()[0][0]
    queue_id_cache[queue] = queue_id

    return queue_id

################################################################################

def set_files_id (filename, size, md5sum, sha1sum, sha256sum, location_id):
    """
    Insert a new entry into the files table.

    Returns the new file_id

    """
    global files_id_cache

    projectB.query("INSERT INTO files (filename, size, md5sum, sha1sum, sha256sum, location) VALUES ('%s', %d, '%s', '%s', '%s', %d)" % (filename, long(size), md5sum, sha1sum, sha256sum, location_id))

    return get_files_id (filename, size, md5sum, location_id)

    ### currval has issues with postgresql 7.1.3 when the table is big
    ### it was taking ~3 seconds to return on auric which is very Not
    ### Cool(tm).
    ##
    ##q = projectB.query("SELECT id FROM files WHERE id = currval('files_id_seq')")
    ##ql = q.getresult()[0]
    ##cache_key = "%s_%d" % (filename, location_id)
    ##files_id_cache[cache_key] = ql[0]
    ##return files_id_cache[cache_key]

################################################################################

def get_maintainer (maintainer_id):
    """ Return the name of the maintainer behind maintainer_id """
    global maintainer_cache

    if not maintainer_cache.has_key(maintainer_id):
        q = projectB.query("SELECT name FROM maintainer WHERE id = %s" % (maintainer_id))
        maintainer_cache[maintainer_id] = q.getresult()[0][0]

    return maintainer_cache[maintainer_id]

################################################################################

def get_suites(pkgname, src=False):
    """ Return the suites in which pkgname is. If src is True, query for source package, else binary. """
    if src:
        sql = """
        SELECT suite_name
        FROM source,
             src_associations,
             suite
        WHERE source.id = src_associations.source
        AND   source.source = '%s'
        AND   src_associations.suite = suite.id
        """ % (pkgname)
    else:
        sql = """
        SELECT suite_name
        FROM binaries,
             bin_associations,
             suite
        WHERE binaries.id = bin_associations.bin
        AND   package = '%s'
        AND   bin_associations.suite = suite.id
        """ % (pkgname)

    q = projectB.query(sql)
    return map(lambda x: x[0], q.getresult())
