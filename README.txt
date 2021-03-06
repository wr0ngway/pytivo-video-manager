PyTivo Video Manager - README.txt

see changelog.txt for a history of changes

what it is
==========

PyTivo video manager (vidmgr) is an HME application that allows you to request that videos in your 
library be "Pushed" to your tivo instead of the normal pull.  Since it's an HME app, this request
can be made from your easy chair with your tivo remote.  Pushing allows videos that are in a
compatible MP4 format to be transferred as is - saving time and space - instead of the transcoding
that a pull will always cause (although a push can also be requested for a video format that requires
transcoding).  vidmgr can also be used to delete videos from your library.

vidmgr was recently upgraded to support shares of type dvdvideo.  Deletion of these videos is not 
supported.

vidmgr is a TiVo HME application designed to operate under wmcbrine's hme for python
framework.  It is NOT a stand-alone application.  Please install the pyhme package (I have tested with version 0.19)
and make sure it is running before you install vidmgr.

Vidmgr is designed to operate in conjunction with the PyTivo transcoding server - If you are not 
using pytivo, then there is no point in installing vidmgr.  I have tested vidmgr with the mcbrine
fork of pytivo.  I am not familiar with the other forks to know whether or not it will run there.

====================================================================================================

installation/setup
==================

If you've gotten this far, you must want to install this.  It's very simple:

1. Go to the directory where you have pyhme installed.  There should be a lot of subdirectories here,
one per application.  Create a new directory here named "vidmgr"

2. Copy the contents of the vidmgr directory tree from this package into this new directory.  This should
include several .py files and a directory named skins.  Within the skins directory, there will be a
directory named orig and a directory named blue.  Each of these will have a bunch of .png files.   BTW,
metadata.py is an extract of the same named file that is part of pytivo.  I can't take the credit for this code.

3. Copy config.merge from this package into the pyhme main directory. 

4. Configure - you will need to merge the config.merge file that was delivered with this package with
your config.ini file that you are currently using.  There are four areas you need to pay attention to:  

	a) You may or may not have an "apps" line under the heading [hmeserver].  If you do not, then
the hmeserver will start all apps that it finds.  If you do, then it will only start the named apps.
So if you do have this line and you do want to run vidmgr, add the word "vidmgr" to this line - no quotes
or commas or other punctuation.

	b) you can specify various vidmgr options by putting entries in the [vidmgr] section of the config.ini
as follows:

[vidmgr]
exts=.mpg .mp4 .avi .wmv .m4v

   this names the file extensions you are interested in
      
descsize=20
   this gives the font point size that will be used for the description text.  20 is the default
   
skin=name
   this is the name of the directory under skins that contains all of the png files that are used
   to draw the screen.  default is "orig", although the package is also shipped with a "blue" skin
   
deleteallowed=true
   this determines whether or not deletion of videos is permitted.  Default is true, set to false
   if you do not want this capability
   
display=value
   determines what information is displayed about videos in the various lists.  allowable values are
   episodetitle  - displays only the episode title
   episodenumtitle - displays the episode number followed by the title
   file - simply displays the filename
   normal - (default) displays program title followed by episode title
   
sort=value
   determines how listings are sorted:
   episodenumber - sort based on episode number - note this is a string sort - not a numeric sort
   file - sort based on the filename
   normal - (default) sorts based on the program title and episode title

metafirst = title seriesTitle episodeTitle description
metaignore = isEpisode isEpisodic
   these two items determine which metadata is displayed first in the info screen and which is ignored. 
   Spelling and case are significant - the name must match exactly.  The default values are those
   values given above
metaspace = name name
metaspaceafter = name name
metaspacebefore = name name
   determines that there should be a blank line in the display before or after the indicated metadata items.  The
   default is an empty list so there will be no blank lines.  metaspace and metaspaceafter are synonyms
metamergefiles = False or True (default = True)
metamergelines = False or True (default = False)
   If there are multiple metafiles that correspond to a video file, these two options control how the data is to be merged.
   metamergefiles = False indicates that the files are not to be merged at all - only the more specific file is to be used.
   If metamergefiles if True, the default value, data from the less specific files is over-written/replaced with data from more
   specific files depending on the value for metamergelines.  If metamergelines is False (the default) then a repeating metadata
   key will REPLACE any previous value read.  If it is true, the new data will be concatenated to the old value separated
   by a space.  Note that metamergelines has NO effect on metadata items that start with a 'v' (vActor, etc).  These data
   items will continue to be processed as arrays.
   
   Metadata files are searched for/processed in the following order:
   	1) .meta/default.txt
   	2) default.txt
   	3) .meta/<title>.txt
   	4) <title>.txt
   Where <title> is the base name of the video file - or "folder" for directories.  DVDVideo shares have a few other
   quirks concerning metadata - see below.
   
infolabelpercent=30
   specifies the width, in percentage of the label field on the info screen.  Default is 30, but I have found that 
   20 works well for HD screens
   
inforightmargin=20
   specifies the width, in pixels of pad area on the right side of the info screen.  Default is 20. 0-100 allowed

thumbjustify=left
   specifies how thumbnail images should be justified.  default = left, can be center or right


	c) You need to tell vidmgr about your Tivos.  For each tivo, you need to specify the name and
the TSN.  The format for this is:
[tivos]
tivo1.name=Family Room
tivo1.tsn=TSN1
tivo2.name=Master Bedroom
tivo2.tsn=TSN2

You can have an arbitrary number of Tivos, but as soon as vidmgr detects a gap in the numbering
sequence it will stop parsing.  Make sure the TSN's are accurate as this is how pytivo knows which
tivo to push to.

	d) You need to tell vidmgr about your PyTivo instances.  There are 4 possible pytivo parameters:
		- config is mandatory and is the fully qualified name of the pytivo config file. 
vidmgr reads this file to determine the share names and locations.  
		- You may specify an ip address for the machine on which this instance of pytivo is running.
If you do not specify one, the local IP address is used.
		- If the pytivo config file names a port in the server section, then vidmgr will
use that port number.  Otherwise you need to specify the port number here.
		-Finally, if your hme server is running in a different host environment than this
instance of pytivo, then you need to specify the directory separator character for the pytivo environment.

format for specifying pytivo information:
[pytivos]
pytivo1.config=/usr/local/pytivo/pyTivo.conf
pytivo1.ip=192.168.1.201
pytivo1.port=9032
pytivo1.sep=/

You can have an arbitrary number of pytivos, but as soon as vidmgr detects a gap in the numbering
sequence it will stop parsing.

A note about the separator:  If you are running both vidmgr and pytivo on the same machine, then this
is not required.  However, if (as was happening while I was developing) you are running vidmgr
in a Windows environment (where the directory separator is unfortunately a backslash '\') and 
you are running pytivo in a linux environment (where the separator is a forward slash '/') then
you need to specify "pytivox.sep=/".  Otherwise, vidmgr will happily send its requests to 
pytivo using a backslash in the paths and this will cause pytivo to choke.

=======================================================================================================

Usage
=====

Vidmgr presents a directory tree to you.  You can step into and out of directories using the normal
tivo navigation keys.  The directory tree is rooted at the list of shares, unless there is only 1 share
in which case it is rooted at the topmost directory of that share.

while on a list of video files, you can also navigate using the number keys.  1 takes you 10% of the
way through the list, 5 = 50%, 7 = 70%, etc.  0 alternately takes you to the end of the list and then to the
beginning of the list

In HD mode, vidmgr will also show video artwork on the right hand side of the screen.  Vidmgr looks for
the following file:  <full-video-file-name-including-extension>.jpg or, if this doesn't exist, folder.jpg.
The view into which this graphic is placed is 620 pixels wide by 450 pixels high.  If your graphic exceeds
those dimensions it will be scaled while maintaining the aspect ratio.  Folder.jpg will also be the thumbnail
used for the enclosing folder or share.  Also, if there is a folder.txt file in a directory, or in the
subtending .meta directory, its contents - notably the description field will be shown on the display
above the thumbnail.

For dvdvideo shares, vidmgr is totally dependent on accurate metadata.  Metadata (and thumbnails) all belong
in the directory containing the VIDEO_TS directory or in a subtending .meta directory.  Metadata is processed
as follows.  default.txt contains the DVD metadata.  __Txx.mpg.txt contains the metadata for title xx.  The
title-specific metadata is overlaid on top of the DVD metadata according to the metamergefiles and metamergefiles
configuration parameters.  The thumbnail for the DVD is in a file named folder.jpg.  In addition, it is
possible to have a thumbnail for a specific title;  the name should be __Txx.mpg.jpg.  If there is no metadata
for a dvdvideo share, vidmgr assumes that there is only 1 title, and its title is the directory name.

Once you choose a video file, you will be shown some of the metadata associated with that file,
and then have two options - push or delete (delete can be disabled - see configuration above).  In
HD mode, this detail will be on the right side of the screen as you navigate through the directories - it
is not on a separate screen

If you choose delete, you will be asked to press thumbs-up to confirm and when you do, the file and
its associated metadata file will be deleted.  If you press ANYTHING other than thumbs-up, the
delete is cancelled.

If you choose push and you only have 1 tivo, then it will simply initiate a push to that tivo and
give you a confirmation message.  If you have multiple tivos, you need to choose the one you want to
push to from the provided list.  After choosing, vidmgr will initiate the push and give you the
confirmation message.  The confirmation message can be dismissed with ANY keypress

At any time on any list or on a details screen, you can press the info button to see a complete
list of the metadata.  You can control which metadata items appear at the front of this display
and which are ignored (see configuration above).  On the info display, you can press left, clear, or info
to return to the screen you came from.  If the information does not fit on one page, you will see
paging cues and you can use either up/down or channel up/down to traverse the pages.
