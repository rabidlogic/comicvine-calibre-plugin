'''
calibre_plugins.comicvine - A calibre metadata source for comicvine
'''
#pylint: disable-msg=R0913,R0904
from functools import partial
import logging

from queue import Queue

from calibre import setup_cli_handlers
from calibre.ebooks.metadata.opf2 import metadata_to_opf
from calibre.ebooks.metadata.sources.base import Source
from calibre.utils.config import OptionParser
import calibre.utils.logging as calibre_logging
from calibre_plugins.mycomicvine.config import PREFS
from calibre_plugins.mycomicvine import utils

class Comicvine(Source):
  ''' Metadata source implementation '''
  name = 'MyComicvine'
  description = 'Downloads metadata and covers from Comicvine'
  author = 'Me'
  version = (0, 11, 2)
  capabilities = frozenset(['identify', 'cover'])
  touched_fields = frozenset([
      'title', 'authors', 'comments', 'publisher', 'pubdate', 'series',
      'identifiers:comicvine', 'identifiers:comicvine-volume',
      ])

  has_html_comments = True
  can_get_multiple_covers = True
  
  def __init__(self, *args, **kwargs):
    self.logger = logging.getLogger('urls')
    self.logger.setLevel(logging.DEBUG)
    self.logger.addHandler(utils.CalibreHandler(logging.DEBUG))
    Source.__init__(self, *args, **kwargs)

  def config_widget(self):
    from calibre_plugins.comicvine.config import ConfigWidget
    return ConfigWidget()

  def save_settings(self, config_widget):
    config_widget.save_settings()

  def is_configured(self):
    return bool(PREFS.get('api_key'))
  
  def _print_result(self, result, opf=False):
    if opf:
      result_text = metadata_to_opf(result)
    else:
      if result.pubdate:
        pubdate = str(result.pubdate.date())
      else:
        pubdate = 'Unknown'
      result_text = '%s: %s [%s]' % (
        result.identifiers['comicvine'], 
        result.title, pubdate)
    print(result_text)


  def cli_main(self, args):
    'Perform comicvine lookups from the calibre-debug cli'
    def option_parser():
      'Parse command line options'
      parser = OptionParser(
        usage='Comicvine [t:title] [a:authors] [i:id]')
      parser.add_option('--opf', '-o', action='store_true', dest='opf')
      parser.add_option('--verbose', '-v', default=False, 
                        action='store_true', dest='verbose')
      parser.add_option('--debug_api', default=False,
                        action='store_true', dest='debug_api')
      return parser

    opts, args = option_parser().parse_args(args)
    if opts.debug_api:
      calibre_logging.default_log = calibre_logging.Log(
        level=calibre_logging.DEBUG)
    if opts.verbose:
      level = 'DEBUG'
    else:
      level = 'INFO'
    setup_cli_handlers(logging.getLogger('comicvine'), 
                       getattr(logging, level))
    log = calibre_logging.ThreadSafeLog(level=getattr(calibre_logging, level))

    (title, authors, ids) = (None, [], {})
    for arg in args:
      if arg.startswith('t:'):
        title = arg.split(':', 1)[1]
    result_queue = Queue()
    self.identify(
      log, result_queue, False, title=title, authors=authors, identifiers=ids)
    for result in result_queue.queue:
      self._print_result(result, opf=opts.opf)
      if opts.opf:
        break


  def identify(self, log, result_queue, abort, 
               title=None, authors=None, identifiers=None, timeout=30):
    '''Attempt to identify comicvine Issue matching given parameters'''
    
    # Do a simple lookup if comicvine identifier present

    if title:
      # Look up candidate volumes based on title
      candidate_issues = utils.find_by_title(title)
      for issue in candidate_issues:
        metadata = utils.build_meta(log, issue)
        if metadata:
          self.clean_downloaded_metadata(metadata)
          result_queue.put(metadata)
    return None

  def download_cover(self, log, result_queue, abort, 
                     title=None, authors=None, identifiers=None, 
                     timeout=30, get_best_cover=False):
    if identifiers and 'comicvine' in identifiers:
      for url in utils.cover_urls(identifiers['comicvine'], get_best_cover):
        #url = 'http://static.comicvine.com' + url
        browser = self.browser
        log('Downloading cover from:', url)
        try:
          cdata = browser.open_novisit(url, timeout=timeout).read()
          result_queue.put((self, cdata))
        except:
          log.exception('Failed to download cover from:', url)

