#!/usr/bin/python
# -*- coding: utf-8 -*-

import glob
import sys
import re
import os
import shutil

BY_CASE_DIR='by_case/'
BY_NAME_DIR='by_name/'
DEBUG = False
JUSTICE_MARKER=r'([A-Z][\'’.A-Z ]+:)'

# to fix stenographer errors
GLOBS = {
    'OCONNOR' : 'JUSTICE_OCONNOR',
    'SOUTER' : 'JUSTICE_SOUTER',
    'SOUR_TER' : 'JUSTICE_SOUTER',
    'SOTOMAYOR': 'JUSTICE_SOTOMAYOR',
    'SCALIA' : 'JUSTICE_SCALIA',
    'SCALIS' : 'JUSTICE_SCALIA',
    'SCAIA' : 'JUSTICE_SCALIA',
    'SC_ALIA' : 'JUSTICE_SCALIA',
    'BREYER' : 'JUSTICE_BREYER',
    'BREYRE' : 'JUSTICE_BREYER',
    'ALITO' : 'JUSTICE_ALITO',
    'GINSBURG' : 'JUSTICE_GINSBURG',
    'REHNQUIST' : 'JUSTICE_REHNQUIST',
    'GINSBERG' : 'JUSTICE_GINSBURG',
    'JUSTICE_ROBERTS' : 'JUSTICE_ROBERTS',
    'JUSTICE_ROBERT' : 'JUSTICE_ROBERTS',
    'JUDGE_ROBERTS' : 'JUSTICE_ROBERTS',
    'JUSTICE_KENNEDY' : 'JUSTICE_KENNEDY',
    'JUSTICE_KENNED' : 'JUSTICE_KENNEDY',
    'JUSTICE_KENNEY' : 'JUSTICE_KENNEDY',
    'JUSTICE_KAGAN' : 'JUSTICE_KAGAN',
    'JUSTICE_STEVENS' : 'JUSTICE_STEVENS',
    'JUSTICE_STEVEN' : 'JUSTICE_STEVENS',
    'JUDGE_STEVENS' : 'JUSTICE_STEVENS',
    'JUSTICE_THOMAS' : 'JUSTICE_THOMAS',
    'JUSTICE_BENNET' : 'MR_BENNETT',
}

JUDGES = ( 
    'JUSTICE_OCONNOR',
    'JUSTICE_KENNEDY',
    'JUSTICE_SOUTER',
    'JUSTICE_STEVENS',
    'JUSTICE_SOTOMAYOR',
    'JUSTICE_SCALIA',
    'JUSTICE_THOMAS',
    'JUSTICE_BREYER',
    'JUSTICE_ALITO',
    'JUSTICE_KAGAN',
    'JUSTICE_GINSBERG',
    'CHIEF_JUSTICE_ROBERTS',
    'CHIEF_JUSTICE_REHNQUIST',
    )

def process_file(f):

    fp = open(f)
    l = [l.rstrip() for l in fp.readlines()]
    fp.close()
    # cruft that we want to ignore
    l = filter(lambda x: x, l)
    l = filter(lambda x: not re.match(r'\d+$', x), l)
    l = filter(lambda x: not re.match(r'Alderson Reporting.*', x), l)
    l = filter(lambda x: not re.match(r'.*Subject to Final Review.*', x), l)
    l = filter(lambda x: not re.match(r'[.,;\'A-Z\s]+$', x), l)
    l = filter(lambda x: not re.match(r'1111 14th Street.*', x), l)
    l = filter(lambda x: not re.match(r'1-800-FOR-DEPO$', x), l)
    l = filter(lambda x: not re.match(r'Washington, DC 20005$', x), l)
    # end cruft

    full_text = ' '.join(l)
    r = re.compile(JUSTICE_MARKER)
    l = r.split(full_text)

    cnt = 0
    for line in l:
        if re.match(JUSTICE_MARKER, line) and \
                not re.match(r'APPEARANCES:',line):
            break
        else:
            cnt += 1
    l = l[cnt:]
    l = zip(l[0::2], l[1::2])

    if len(l) == 0:
        print "ERROR: no transcript found"
        sys.exit(255)

    # create dir for by_case (based on the file)
    file_dir = os.path.splitext(f)[0]
    file_dir = BY_CASE_DIR + os.path.basename(file_dir)
    os.makedirs(file_dir)
 
    for transcript in l:
        debug("person ->" + transcript[0] + "<-")
        debug("text ->" + transcript[1] + "<-")
        name = transcript[0]
        text = transcript[1]
        # remove cruft at the end of the transcript if applicable
        text = re.sub(r'\s*The\s+case\s+is\s+submitted.*', '', text)
        text = re.sub(r'\s*above-entitled matter was submitted.*', '', text)
        # remove other cruft
        text = re.sub(r'1', '', text)
        text = re.sub(r'^\s+', '', text)
         
        # if the transcript is empty move to the next one
        if not text:
            continue
        else:
            text = text + '\n'

        # munge the name so it's better for a filename
        name = re.sub(r'[\'’.,;:]','', name)
        name = re.sub(r'^\s+','', name)
        name = re.sub(r' ','_', name)

        for glob in GLOBS:
            if re.search(glob, name):
                name = re.sub(r'.*' + glob + r'.*', GLOBS[glob], name)
                break

        # if it's a justice and there is a "Your Honor" in
        # the text we can assume it's not something we want
        # to keep

        if re.search('JUSTICE', name) and re.search('Your Honor', text):
            continue
        
        # if the name is just "JUSTICE" there isn't much we
        # can do, so we will skip it
        if re.search('^JUSTICE$', name):
            continue

        file_path = file_dir + "/" + name
        try:
            fp = open(file_path,'a')
            fp.write(text)
        except IOError:
            print "Unable to write to " + file_path + \
                    "\nname ->" + name + "<-"
            sys.exit(255)
        fp.close()

        file_path_person = BY_NAME_DIR + "/" + name
        try:
            fp = open(file_path_person,'a')
            fp.write(text)
        except IOError:
            print "Unable to write to " + file_path_person + \
                    "\nname ->" + name + "<-"
            sys.exit(255)


def debug(line):
    if DEBUG:
        print line

def main():

    shutil.rmtree(BY_CASE_DIR, ignore_errors=True)
    shutil.rmtree(BY_NAME_DIR, ignore_errors=True)
    os.makedirs(BY_NAME_DIR)

    flist = glob.glob('/home/jarv/prog/scotus/pdfs/*.txt')
    #process_file('/home/jarv/prog/scotus/pdfs/08-1498.txt')
    map(process_file, flist)

if __name__ == '__main__': sys.exit(main())
