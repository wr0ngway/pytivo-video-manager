PyTivo Video Manager

what it is
==========

PyTivo video manager (vidmgr) is an HME application that allows you to request that videos in your 
library be "Pushed" to your tivo instead of the normal pull.  SInce it's an HME app, this request
can be made from your easy chair with your tivo remote.  Pushing allows videos that are in a
compatible MP4 format to be transferred as is - saving time and space - instead of the transcoding
that a pull will always cause.  vidmgr can also be used to delete videos from your library.

vidmgr is a TiVo HME application designed to operate under wmcbrine's pyhme
framework.  It is NOT a stand-alone application.  Please install the pyhme package and make sure it
is running before you install vidmgr.

Vidmgr is designed to operate in conjunction with the PyTivo transcoding server - If you are not 
using pytivo, then there is no point in installing vidmgr.  I have tested vidmgr with the mcbrine
fork of pytivo.  I am not familiar with the other forks to know whether or not it will run there.

====================================================================================================

installation/setup
==================

If you've gotten this far, you must want to really install this.  It's very simple:

1. Go to the directory where you have pyhme installed.  There should be a lot of subdirectories here,
one per application.  Create a new directroy here named "vidmgr"

2. Copy the contents of the vidmgr directory from this package into this new directory.  This should
include __init__.py and a bunch of .png files

3. Copy metadata.py and config.merge from this package into the pyhme main directory.  BTW - metadata.py
is an extract of the same named file that is part of pytivo.  I can't take the credit for this code.

4. Configure - you will need to merge the config.merge file that was delivered with this package with
your config.ini file that you are currently using.  There are three areas you need to pay attention to:  

	a) You may or may not have an "apps" line under the heading [hmeserver].  If you do not, then
the hmeserver will start all apps that it finds.  If you do, then it will only start the named apps.
So if you do have this line and you do want to run vidmgr, add the word "vidmgr" to this line - no quotes
or commas or other punctuation.

	b) You need to tell vidmgr about your Tivos.  For each tivo, you need to specify the name and
the TSN.  The format for this is:
[tivos]
tivo1.name=Family Room
tivo1.tsn=TSN1
tivo2.name=Master Bedroom
tivo2.tsn=TSN2

You can have an arbitrary number of Tivos, but as soon as vidmgr detects a gap in the numbering
sequence it will stop parsing.  Make sure the TSN's are accurate as this is how pytivo knows which
tivo to push to.

	c) You need to tell vidmgr about your PyTivo instances.  There are 4 possible pytivo parameters:
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
tivo navigation keys.  The directory tree is rooted at ths list of shares, unless there is only 1 share
in which case it is rooted at the topmost directory of that share.

Once you choose a video file, you will be shown some of the metadata associated with that file,
and then have two options - push or delete.

If you choose delete, you will be asked to press thumbs-up to confirm and when you do, the file and
its associated metadata file will be deleted.  If you press ANYTHING other than thumbs-up, the
delete is cancelled.

If you choose push and you only have 1 tivo, then it will simply initiate a push to that tivo and
give you a confirmation message.  If you have multiple tivos, you need to choose the one you want to
push to from the provided list.  After choosing, vidmgr will initiate the push and give you the
confirmation message.  The confirmation message can be dismissed with ANY keypress