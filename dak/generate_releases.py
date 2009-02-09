#!/usr/bin/env python

""" Create all the Release files """

# Copyright (C) 2001, 2002, 2006  Anthony Towns <ajt@debian.org>

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

#   ``Bored now''

################################################################################

import sys, os, stat, time, pg
import gzip, bz2
import apt_pkg
from daklib import utils
from daklib.dak_exceptions import *

################################################################################

Cnf = None
projectB = None
out = None
AptCnf = None

################################################################################

def usage (exit_code=0):
    print """Usage: dak generate-releases [OPTION]... [SUITE]...
Generate Release files (for SUITE).

  -h, --help                 show this help and exit
  -a, --apt-conf FILE        use FILE instead of default apt.conf
  -f, --force-touch          ignore Untouchable directives in dak.conf

If no SUITE is given Release files are generated for all suites."""

    sys.exit(exit_code)

################################################################################

def add_tiffani (files, path, indexstem):
    index = "%s.diff/Index" % (indexstem)
    filepath = "%s/%s" % (path, index)
    if os.path.exists(filepath):
        #print "ALERT: there was a tiffani file %s" % (filepath)
        files.append(index)

def compressnames (tree,type,file):
    compress = AptCnf.get("%s::%s::Compress" % (tree,type), AptCnf.get("Default::%s::Compress" % (type), ". gzip"))
    result = []
    cl = compress.split()
    uncompress = ("." not in cl)
    for mode in compress.split():
        if mode == ".":
            result.append(file)
        elif mode == "gzip":
            if uncompress:
                result.append("<zcat/.gz>" + file)
                uncompress = 0
            result.append(file + ".gz")
        elif mode == "bzip2":
            if uncompress:
                result.append("<bzcat/.bz2>" + file)
                uncompress = 0
            result.append(file + ".bz2")
    return result

decompressors = { 'zcat' : gzip.GzipFile,
                  'bzip2' : bz2.BZ2File }

def print_md5sha_files (tree, files, hashop):
    path = Cnf["Dir::Root"] + tree + "/"
    for name in files:
        hashvalue = ""
        hashlen = 0
        try:
            if name[0] == "<":
                j = name.index("/")
                k = name.index(">")
                (cat, ext, name) = (name[1:j], name[j+1:k], name[k+1:])
                file_handle = decompressors[ cat ]( "%s%s%s" % (path, name, ext) )
                contents = file_handle.read()
                hashvalue = hashop(contents)
                hashlen = len(contents)
            else:
                try:
                    file_handle = utils.open_file(path + name)
                    hashvalue = hashop(file_handle)
                    hashlen = os.stat(path + name).st_size
                except:
                    raise
                else:
                    if file_handle:
                        file_handle.close()

        except CantOpenError:
            print "ALERT: Couldn't open " + path + name
        else:
            out.write(" %s %8d %s\n" % (hashvalue, hashlen, name))

def print_md5_files (tree, files):
    print_md5sha_files (tree, files, apt_pkg.md5sum)

def print_sha1_files (tree, files):
    print_md5sha_files (tree, files, apt_pkg.sha1sum)

def print_sha256_files (tree, files):
    print_md5sha_files (tree, files, apt_pkg.sha256sum)

################################################################################

def main ():
    global Cnf, AptCnf, projectB, out
    out = sys.stdout

    Cnf = utils.get_conf()

    Arguments = [('h',"help","Generate-Releases::Options::Help"),
                 ('a',"apt-conf","Generate-Releases::Options::Apt-Conf", "HasArg"),
                 ('f',"force-touch","Generate-Releases::Options::Force-Touch"),
                ]
    for i in [ "help", "apt-conf", "force-touch" ]:
        if not Cnf.has_key("Generate-Releases::Options::%s" % (i)):
            Cnf["Generate-Releases::Options::%s" % (i)] = ""

    suites = apt_pkg.ParseCommandLine(Cnf,Arguments,sys.argv)
    Options = Cnf.SubTree("Generate-Releases::Options")

    if Options["Help"]:
        usage()

    if not Options["Apt-Conf"]:
        Options["Apt-Conf"] = utils.which_apt_conf_file()

    AptCnf = apt_pkg.newConfiguration()
    apt_pkg.ReadConfigFileISC(AptCnf, Options["Apt-Conf"])

    projectB = pg.connect(Cnf["DB::Name"], Cnf["DB::Host"], int(Cnf["DB::Port"]))

    if not suites:
        suites = Cnf.SubTree("Suite").List()

    for suite in suites:
        print "Processing: " + suite
        SuiteBlock = Cnf.SubTree("Suite::" + suite)

        if SuiteBlock.has_key("Untouchable") and not Options["Force-Touch"]:
            print "Skipping: " + suite + " (untouchable)"
            continue

        suite = suite.lower()

        origin = SuiteBlock["Origin"]
        label = SuiteBlock.get("Label", origin)
        codename = SuiteBlock.get("CodeName", "")

        version = ""
        description = ""

        q = projectB.query("SELECT version, description FROM suite WHERE suite_name = '%s'" % (suite))
        qs = q.getresult()
        if len(qs) == 1:
            if qs[0][0] != "-": version = qs[0][0]
            if qs[0][1]: description = qs[0][1]

        if SuiteBlock.has_key("NotAutomatic"):
            notautomatic = "yes"
        else:
            notautomatic = ""

        if SuiteBlock.has_key("Components"):
            components = SuiteBlock.ValueList("Components")
        else:
            components = []

        suite_suffix = Cnf.Find("Dinstall::SuiteSuffix")
        if components and suite_suffix:
            longsuite = suite + "/" + suite_suffix
        else:
            longsuite = suite

        tree = SuiteBlock.get("Tree", "dists/%s" % (longsuite))

        if AptCnf.has_key("tree::%s" % (tree)):
            pass
        elif AptCnf.has_key("bindirectory::%s" % (tree)):
            pass
        else:
            aptcnf_filename = os.path.basename(utils.which_apt_conf_file())
            print "ALERT: suite %s not in %s, nor untouchable!" % (suite, aptcnf_filename)
            continue

        print Cnf["Dir::Root"] + tree + "/Release"
        out = open(Cnf["Dir::Root"] + tree + "/Release", "w")

        out.write("Origin: %s\n" % (origin))
        out.write("Label: %s\n" % (label))
        out.write("Suite: %s\n" % (suite))
        if version != "":
            out.write("Version: %s\n" % (version))
        if codename != "":
            out.write("Codename: %s\n" % (codename))
        out.write("Date: %s\n" % (time.strftime("%a, %d %b %Y %H:%M:%S UTC", time.gmtime(time.time()))))

        if SuiteBlock.has_key("ValidTime"):
            validtime=float(SuiteBlock["ValidTime"])
            out.write("Valid-Until: %s\n" % (time.strftime("%a, %d %b %Y %H:%M:%S UTC", time.gmtime(time.time()+validtime))))

        if notautomatic != "":
            out.write("NotAutomatic: %s\n" % (notautomatic))
        out.write("Architectures: %s\n" % (" ".join(filter(utils.real_arch, SuiteBlock.ValueList("Architectures")))))
        if components:
            out.write("Components: %s\n" % (" ".join(components)))

        if description:
            out.write("Description: %s\n" % (description))

        files = []

        if AptCnf.has_key("tree::%s" % (tree)):
            for sec in AptCnf["tree::%s::Sections" % (tree)].split():
                for arch in AptCnf["tree::%s::Architectures" % (tree)].split():
                    if arch == "source":
                        filepath = "%s/%s/Sources" % (sec, arch)
                        for cfile in compressnames("tree::%s" % (tree), "Sources", filepath):
                            files.append(cfile)
                        add_tiffani(files, Cnf["Dir::Root"] + tree, filepath)
                    else:
                        disks = "%s/disks-%s" % (sec, arch)
                        diskspath = Cnf["Dir::Root"]+tree+"/"+disks
                        if os.path.exists(diskspath):
                            for dir in os.listdir(diskspath):
                                if os.path.exists("%s/%s/md5sum.txt" % (diskspath, dir)):
                                    files.append("%s/%s/md5sum.txt" % (disks, dir))

                        filepath = "%s/binary-%s/Packages" % (sec, arch)
                        for cfile in compressnames("tree::%s" % (tree), "Packages", filepath):
                            files.append(cfile)
                        add_tiffani(files, Cnf["Dir::Root"] + tree, filepath)

                    if arch == "source":
                        rel = "%s/%s/Release" % (sec, arch)
                    else:
                        rel = "%s/binary-%s/Release" % (sec, arch)
                    relpath = Cnf["Dir::Root"]+tree+"/"+rel

                    try:
                        if os.access(relpath, os.F_OK):
                            if os.stat(relpath).st_nlink > 1:
                                os.unlink(relpath)
                        release = open(relpath, "w")
                        #release = open(longsuite.replace("/","_") + "_" + arch + "_" + sec + "_Release", "w")
                    except IOError:
                        utils.fubar("Couldn't write to " + relpath)

                    release.write("Archive: %s\n" % (suite))
                    if version != "":
                        release.write("Version: %s\n" % (version))
                    if suite_suffix:
                        release.write("Component: %s/%s\n" % (suite_suffix,sec))
                    else:
                        release.write("Component: %s\n" % (sec))
                    release.write("Origin: %s\n" % (origin))
                    release.write("Label: %s\n" % (label))
                    if notautomatic != "":
                        release.write("NotAutomatic: %s\n" % (notautomatic))
                    release.write("Architecture: %s\n" % (arch))
                    release.close()
                    files.append(rel)

            if AptCnf.has_key("tree::%s/main" % (tree)):
                for dis in ["main", "contrib", "non-free"]:
                    if not AptCnf.has_key("tree::%s/%s" % (tree, dis)): continue
                    sec = AptCnf["tree::%s/%s::Sections" % (tree,dis)].split()[0]
                    if sec != "debian-installer":
                        print "ALERT: weird non debian-installer section in %s" % (tree)

                    for arch in AptCnf["tree::%s/%s::Architectures" % (tree,dis)].split():
                        if arch != "source":  # always true
                            for cfile in compressnames("tree::%s/%s" % (tree,dis),
                                "Packages",
                                "%s/%s/binary-%s/Packages" % (dis, sec, arch)):
                                files.append(cfile)
            elif AptCnf.has_key("tree::%s::FakeDI" % (tree)):
                usetree = AptCnf["tree::%s::FakeDI" % (tree)]
                sec = AptCnf["tree::%s/main::Sections" % (usetree)].split()[0]
                if sec != "debian-installer":
                    print "ALERT: weird non debian-installer section in %s" % (usetree)

                for arch in AptCnf["tree::%s/main::Architectures" % (usetree)].split():
                    if arch != "source":  # always true
                        for cfile in compressnames("tree::%s/main" % (usetree), "Packages", "main/%s/binary-%s/Packages" % (sec, arch)):
                            files.append(cfile)

        elif AptCnf.has_key("bindirectory::%s" % (tree)):
            for cfile in compressnames("bindirectory::%s" % (tree), "Packages", AptCnf["bindirectory::%s::Packages" % (tree)]):
                files.append(cfile.replace(tree+"/","",1))
            for cfile in compressnames("bindirectory::%s" % (tree), "Sources", AptCnf["bindirectory::%s::Sources" % (tree)]):
                files.append(cfile.replace(tree+"/","",1))
        else:
            print "ALERT: no tree/bindirectory for %s" % (tree)

        out.write("MD5Sum:\n")
        print_md5_files(tree, files)
        out.write("SHA1:\n")
        print_sha1_files(tree, files)
        out.write("SHA256:\n")
        print_sha256_files(tree, files)

        out.close()
        if Cnf.has_key("Dinstall::SigningKeyring"):
            keyring = "--secret-keyring \"%s\"" % Cnf["Dinstall::SigningKeyring"]
            if Cnf.has_key("Dinstall::SigningPubKeyring"):
                keyring += " --keyring \"%s\"" % Cnf["Dinstall::SigningPubKeyring"]

            arguments = "--no-options --batch --no-tty --armour"
            if Cnf.has_key("Dinstall::SigningKeyIds"):
                signkeyids = Cnf["Dinstall::SigningKeyIds"].split()
            else:
                signkeyids = [""]

            dest = Cnf["Dir::Root"] + tree + "/Release.gpg"
            if os.path.exists(dest):
                os.unlink(dest)

            for keyid in signkeyids:
                if keyid != "": defkeyid = "--default-key %s" % keyid
                else: defkeyid = ""
                os.system("gpg %s %s %s --detach-sign <%s >>%s" %
                        (keyring, defkeyid, arguments,
                        Cnf["Dir::Root"] + tree + "/Release", dest))

#######################################################################################

if __name__ == '__main__':
    main()
