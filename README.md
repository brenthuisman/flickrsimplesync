## flickrsimplesync - Sync/backup your photos to flickr easily

flickrsimplesync is a tool you can use to easily sync up or down your
photos in a drive/folder to flickr since now it has a free 1TB storage
you can probably sync all your photo collection.


### Install

Simply run the following:

    $ python setup.py install

Or run directly with:

    $ python lastfmtagupdater

### Example Usage

Both run from source and command line have same parameters:

    start uploading all photos/videos under that folder
    $ flickrsimplesync

    ignore videos for others use --help
    $ flickrsimplesync --ignore-videos

    start downloading all photos on flickr to that folder
    $ flickrsimplesync --download .
    
    start downloading all paths starting with that path
    $ flickrsimplesync --download 2008/2008-01-01


### Changelog

3.0 (2016-03-21)
 * Ported to Python v3, FlickrApi v2
 * Renamed to flickrsimplesync
 * Removed dependency on IPTCInfo, tag filtering option removed
 * Removed file system monitoring
 * Removed logging module, using print() and sys.stderr.write()

0.1.17-2 (2014-09-06)
 * Use Flickrs privacy preferences as a default setting for flicksmartsync
 * Pull request refused: https://github.com/faisalraja/flickrsmartsync/pull/28
 * Forked from https://github.com/faisalraja/flickrsmartsync

0.1.17 (2014-08-12)
 * allow filtering files to upload by IPTC keyword (thanks ricardokirkner)
 * updated flickrapi 1.4.4

0.1.16 (2014-06-30)
 * flickr api changes use https

0.1.15 (2014-05-30)
 * monitor folder support (--monitor)

0.1.14.3 (2014-05-18)
 * encoding bug

0.1.14.2 (2014-04-15)
 * send script output to syslog for headless convience (thanks dahlb)

0.1.14 (2014-02-25)
 * added --starts-with param
 * added --version param
 * bug fix not uploading files properly

0.1.12 (2014-02-15)
 * added custom set title
 * character encoding bugs
 * skip failures

0.1.11 (2013-07-09)

 * added mts video
 * added folder utf8 encoding to avoid dups
 * added sorting for each folders

0.1.10 (2013-07-07)

 * sorted photo sets
 * ignore files > 1gb

0.1.9 (2013-06-28)

 * added --sync-path param

0.1.8 (2013-06-25)

 * ignore hidden folders/folders
 * added video support
 * added new params for skipping video/images

0.1.7 (2013-06-15)

 * added run from source

0.1 (2013-06-13)
