# Comicvine
A calibre metadata source plugin for comicvine.com

## Install

On a Unix system this can be done using:

    $ zip Comicvine -@ < MANIFEST
    $ calibre-customize -a Comicvine.zip

The single command `calibre-customize -b .` from within the source
directory will also work, but will include many unnecessary files.

## Usage 

Allows you to search comicvine for metadata for your comics and
graphic novels stored in Calibre.

You will need an API Key to use this source
 
Get one at (http://www.comicvine.com/api/)

Once configured you can use this plugin from the GUI (download
metadata) or from the fetch-ebook-metadata command.  

Both of these methods will try all active metadata sources, and only
return the most preferred result.

Only searches the Title. 

## Contribute 

You can contribute by submitting issue tickets on GitHub
(https://github.com/authmillenon/pycomicvine), including Pull
Requests. You can test the comicvine plugin by calling:

    calibre-debug -e __init__.py

