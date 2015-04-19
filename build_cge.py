#! /bin/usr/env python
# D.J. Bennett
# 19/04/2015
"""
Build docs for the CGE website from the /BES-QSIG/docs repository.

Usage:
python build_cge.py
jekyll build

Then, upload _site/ to gh-pages branch.
"""

# LIBS
import os
import re
import sys
import subprocess
import operator

# GLOBALS
front_matter = """---
layout: doc
authors: {0}
lastchange: {1}
title: {2}
permalink: /docs/{3}/
---
"""


# FUNCTIONS
def get_contributions(doc_path, input_dir):
    """Return string of authors and their percentage contributions"""
    # read git log
    cmd = 'git log --stat {0}'.format(doc_path)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               shell=True, stderr=subprocess.PIPE,
                               cwd=input_dir)
    gitlog, _ = process.communicate()
    # split into different commits
    commits = re.split('commit\s[a-zA-Z0-9]+\n', gitlog)
    # get number of changes by name
    name_changes = {}
    for commit in commits[1:]:
        # split into lines
        lines = commit.strip().split('\n')
        # search first line for author
        name_start = re.search('^Author:\s', lines[0]).end()
        name_end = re.search('^Author:\s.*\s<', lines[0]).end() - 1
        name = lines[0][name_start:name_end].strip()
        # search penultimate line for changes to file
        changes_start = re.search(doc_path + '\s\|\s', lines[-2]).end()
        changes_end = re.search(doc_path + '\s\|\s[0-9]+\s', lines[-2]).end()
        changes = int(lines[-2][changes_start:changes_end].strip())
        if name in name_changes.keys():
            name_changes[name] += changes
        else:
            name_changes[name] = changes
    # convert into rough %
    total = sum(name_changes.values())
    for name in name_changes.keys():
        name_changes[name] = name_changes[name]*100/total
    # sort by who made most contributions
    sorted_by_changes = sorted(name_changes.items(),
                               key=operator.itemgetter(1))
    sorted_by_changes.reverse()
    # unpack
    author_string = ''
    for e in sorted_by_changes:
        author_string += '{0} ({1}%), '.format(e[0], e[1])
    return(author_string.strip(', '))


def get_last_change(doc_path, input_dir):
    """Return string of date since last edit"""
    # read git log with formatter
    cmd = 'git log --pretty=format:"%ad" {0}'.format(doc_path)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               shell=True, stderr=subprocess.PIPE,
                               cwd=input_dir)
    gitlog, _ = process.communicate()
    # split into different commits
    commits = re.split('\n', gitlog)
    # take first of the list
    last_change = commits[0]
    # extract date and year (ignore time)
    last_change = last_change[0:9] + ', ' + last_change[20:24]
    return(last_change)


def read_doc(doc_path, input_dir):
    """Return string of doc text without any front-matter"""
    pattern = re.compile('\-\-\-')
    with open(os.path.join(input_dir, doc_path), 'rb') as f:
        text = f.read()
    res = pattern.search(text)
    if res:
        # there should be two ---, else this will raise an error
        text = text[res.end():]
        res = pattern.search(text)
        text = text[res.end():]
    return(text[1:])


def run(input_dir, output_dir):
    """Make docs in _docs_repo/ CGE friendly"""
    # get docs
    docs = [e for e in os.listdir(input_dir) if re.search('\.md', e)]
    docs = [e for e in docs if docs != 'README.md']
    for doc in docs:
        # get metadata
        authors = get_contributions(doc, input_dir)
        last_change = get_last_change(doc, input_dir)
        title = doc.replace('_', ' ')
        title = title.replace('.md', '')
        title = title.title()
        # construct front-matter
        doc_fm = front_matter.format(authors, last_change, title,
                                     doc.replace('.md', ''))
        # read doc
        doc_text = read_doc(doc, input_dir)
        # combine
        new_doc = doc_fm + doc_text
        # write out
        with open(os.path.join(output_dir, doc), 'wb') as f:
            f.write(new_doc)

if __name__ == '__main__':
    if os.getcwd()[-3:] != 'cge':
        sys.exit('Must only be run in cge/!')
    # sort dirs
    input_dir = os.path.join(os.getcwd(), '_docs_repo')
    if '_docs_repo' not in os.listdir(os.getcwd()):
        sys.exit('No _docs_repo/ found in cwd.')
    output_dir = os.path.join(os.getcwd(), '_docs')
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    # run
    run(input_dir=input_dir, output_dir=output_dir)
