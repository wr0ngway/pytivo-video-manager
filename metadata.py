#!/usr/bin/env python

import os
from datetime import datetime

# Something to strip
TV_RATINGS = {'TV-Y7': 'x1', 'TV-Y': 'x2', 'TV-G': 'x3', 'TV-PG': 'x4', 
              'TV-14': 'x5', 'TV-MA': 'x6', 'TV-NR': 'x7',
              'TVY7': 'x1', 'TVY': 'x2', 'TVG': 'x3', 'TVPG': 'x4', 
              'TV14': 'x5', 'TVMA': 'x6', 'TVNR': 'x7',
              'Y7': 'x1', 'Y': 'x2', 'G': 'x3', 'PG': 'x4',
              '14': 'x5', 'MA': 'x6', 'NR': 'x7', 'UNRATED': 'x7'}

MPAA_RATINGS = {'G': 'G1', 'PG': 'P2', 'PG-13': 'P3', 'PG13': 'P3',
                'R': 'R4', 'X': 'X5', 'NC-17': 'N6', 'NC17': 'N6',
                'NR': 'N8', 'UNRATED': 'N8'}

STAR_RATINGS = {'1': 'x1', '1.5': 'x2', '2': 'x3', '2.5': 'x4',
                '3': 'x5', '3.5': 'x6', '4': 'x7',
                '*': 'x1', '**': 'x3', '***': 'x5', '****': 'x7'}

HUMAN = {'mpaaRating': {'G1': 'G', 'P2': 'PG', 'P3': 'PG-13', 'R4': 'R',
                        'X5': 'X', 'N6': 'NC-17', 'N8': 'Unrated'},
         'tvRating': {'x1': 'TV-Y7', 'x2': 'TV-Y', 'x3': 'TV-G',
                      'x4': 'TV-PG', 'x5': 'TV-14', 'x6': 'TV-MA',
                      'x7': 'Unrated'},
         'starRating': {'x1': '1', 'x2': '1.5', 'x3': '2', 'x4': '2.5',
                        'x5': '3', 'x6': '3.5', 'x7': '4'}}

BOM = '\xef\xbb\xbf'

def tag_data(element, tag):
    for name in tag.split('/'):
        new_element = element.getElementsByTagName(name)
        if not new_element:
            return ''
        element = new_element[0]
    if not element.firstChild:
        return ''
    return element.firstChild.data

def _vtag_data(element, tag):
    for name in tag.split('/'):
        new_element = element.getElementsByTagName(name)
        if not new_element:
            return []
        element = new_element[0]
    elements = element.getElementsByTagName('element')
    return [x.firstChild.data for x in elements if x.firstChild]

def _tag_value(element, tag):
    item = element.getElementsByTagName(tag)
    if item:
        value = item[0].attributes['value'].value
        name = item[0].firstChild.data
        return name[0] + value[0]

def from_text(full_path):
    metadata = {}
    path, name = os.path.split(unicode(full_path, 'utf-8'))
    title, ext = os.path.splitext(name)

    for metafile in [os.path.join(path, title) + '.properties',
                     os.path.join(path, 'default.txt'), full_path + '.txt',
                     os.path.join(path, '.meta', 'default.txt'),
                     os.path.join(path, '.meta', name) + '.txt']:
        if os.path.exists(metafile):
            sep = ':='[metafile.endswith('.properties')]
            for line in file(metafile, 'U'):
                if line.startswith(BOM):
                    line = line[3:]
                if line.strip().startswith('#') or not sep in line:
                    continue
                key, value = [x.strip() for x in line.split(sep, 1)]
                if not key or not value:
                    continue
                if key.startswith('v'):
                    if key in metadata:
                        metadata[key].append(value)
                    else:
                        metadata[key] = [value]
                else:
                    metadata[key] = value

    for rating, ratings in [('tvRating', TV_RATINGS),
                            ('mpaaRating', MPAA_RATINGS),
                            ('starRating', STAR_RATINGS)]:
        x = metadata.get(rating, '').upper()
        if x in ratings:
            metadata[rating] = ratings[x]

    return metadata

def basic(full_path):
    base_path, name = os.path.split(full_path)
    title, ext = os.path.splitext(name)
    mtime = os.stat(unicode(full_path, 'utf-8')).st_mtime
    if (mtime < 0):
        mtime = 0
    originalAirDate = datetime.fromtimestamp(mtime)

    metadata = {'title': title,
                'originalAirDate': originalAirDate.isoformat()}

    return metadata

