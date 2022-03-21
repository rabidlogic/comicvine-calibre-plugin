'''
calibre_plugins.comicvine - A calibre metadata source for comicvine
'''
import logging
import random
import re
import time
import datetime

import json
import urllib.request as urllib2

from urllib.parse import urlencode

from calibre.ebooks.metadata.book.base import Metadata
from calibre.utils import logging as calibre_logging # pylint: disable=W0404
from calibre.utils.config import JSONConfig
from calibre_plugins.comicvine.config import PREFS

# Optional Import for fuzzy title matching
try:
  import Levenshtein
except ImportError:
  pass

class CalibreHandler(logging.Handler):
  '''
  python logging handler that directs messages to the calibre logging
  interface
  '''
  def emit(self, record):
    level = getattr(calibre_logging, record.levelname)
    calibre_logging.default_log.prints(level, record.getMessage())

api_host = "https://comicvine.gamespot.com/api"

default_params = {
  "api_key" : PREFS.get('api_key'),
  "format" : "json"
}

def api_call(url, params):
  for term in default_params.keys():
    params[term] = default_params[term]

  headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
  }

  params = urlencode(params)
  url = url + "?" + params
  req = urllib2.Request(url)
  req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36')
  r = json.loads(urllib2.urlopen(req).read())
  
  if (type(r) == dict):
    if "results" in r:
      if type(r["results"]) == list:
        return r["results"]
      else:
        return [ r["results"] ]
  return []

def find_by_title(title):
  url = "%s/search/" % (api_host)
  issue_meta = []
  issues = api_call(url, {"resources" : "issue", "query" : title, "field_list" : "api_detail_url"})
  for issue in issues:
    i_data = api_call(issue["api_detail_url"], {})
    if len(i_data) == 1:
      v_data = api_call(i_data[0]["volume"]["api_detail_url"], {})
      i_data[0]["volume"] = v_data[0]
      issue_meta.append(i_data[0])

  return issue_meta

def find_by_id(id):
  url = "%s/issue/4000-%s" % (api_host, str(id))
  issue = api_call(url, {})
  return issue[0]

def build_meta(log, issue):
  '''Build metadata record based on comicvine issue_id'''
  title = '%s #%s' %  (issue["volume"]["name"], issue["issue_number"])
  if issue["name"]:
    title = title + ': %s' % (issue["name"])
  authors = [p["name"] for p in issue["person_credits"]]
  meta = Metadata(title, authors)
  meta.series = issue["volume"]["name"]
  meta.series_index = str(issue["issue_number"])
  meta.set_identifier('comicvine', str(issue["id"]))
  meta.set_identifier('comicvine-volume', str(issue["volume"]["id"]))
  meta.tags.append("Comics")
  meta.comments = issue["description"]
  if issue["image"]:
    meta.has_cover = True
  else:
    meta.has_cover = False
  if issue["volume"]["publisher"]:
    meta.publisher = issue["volume"]["publisher"]["name"]
  if issue["store_date"] or issue["cover_date"]:
    meta.pubdate = issue["store_date"] or issue["cover_date"]
    log("Pubdate before parse: %s" % meta.pubdate)
    meta.pubdate = datetime.datetime.strptime(meta.pubdate, '%Y-%m-%d')
  return meta

# Do not include the retry decorator for generator, as exceptions in
# generators are always fatal.  Functions that use this should be
# decorated instead.
def cover_urls(comicvine_id, get_best_cover=False):
  'Retrieve cover urls for comic in quality order'
  issue = find_by_id(comicvine_id)
  for url in ['super_url', 'medium_url', 'small_url']:
    if url in issue["image"]:
      yield issue["image"][url]
      if get_best_cover:
        break
  
