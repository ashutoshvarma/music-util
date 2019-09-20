#Imports
import os, sys
import importlib
import inspect
import warnings
from enum import Enum
from itertools import chain

import requests
from bs4 import BeautifulSoup as bs, element, NavigableString
import json

try:
    from .util import get_inner_texts, convert_size, Cache
except (ModuleNotFoundError, ImportError):
    from util import get_inner_texts, convert_size, Cache

SOURCES = {}
SRC_DEFAULT = 'chiasenhac_vn'

_NO_SOURCE_WARNING = ("No Music Source found. "
                      "Make sure there is atleast one class "
                      "inheriting 'BaseSource'. ")


class SourceException(Exception):
    """Base exception for music sources error."""

    def __init__(self, http_status, code, msg, headers=None):
        self.http_status = http_status
        self.code = code
        self.msg = msg

        if headers is None:
            headers = {}
        self.headers = headers

    def __str__(self):
        return 'Http Status: {0}, Code:{1} => {2}'.format(
            self.http_status, self.code, self.msg)


class BaseSource(object):
    def __init__(self,
                 prefix,
                 header,
                 name="",
                 trace=False,
                 trace_out=False,
                 requests_session=None,
                 proxies=None,
                 requests_timeout=None):
        self.name = name
        self.basename = name
        self.trace = trace
        self.trace_out = trace_out
        self.proxies = proxies
        self.requests_timeout = requests_timeout

        assert prefix
        self.prefix = prefix

        assert isinstance(header, dict)
        self.header = header

        if isinstance(requests_session, requests.Session):
            self._session = requests_session
        else:
            if requests_session:  # Build a new session.
                self._session = requests.Session()
            else:  # Use the Requests API module as a "session".
                from requests import api
                self._session = api


class BaseSourceScrapper(BaseSource):
    """Base class for all music sources."""

    def __init__(self,
                 prefix,
                 header,
                 name="",
                 trace=False,
                 trace_out=False,
                 requests_session=None,
                 proxies=None,
                 requests_timeout=None):
        super().__init__(self._PREFIX, self._HEADERS, self._NAME, trace,
                         trace_out, requests_session, proxies,
                         requests_timeout)

    def _internal_call(self, method, url, return_json, payload, params):
        args = dict(params=params)
        args["timeout"] = self.requests_timeout

        headers = self.header
        headers['Host'] = url.split('/')[2]
        if return_json:
            headers['Content-Type'] = 'application/json'

        if not url.startswith('http'):
            url = self.prefix + url

        if payload:
            args["data"] = json.dumps(payload)

        r = self._session.request(
            method, url, headers=headers, proxies=self.proxies, **args)

        if self.trace_out:
            print("Base url :", url)

        if self.trace:  # pragma: no cover
            print()
            print('headers:\n{}'.format(json.dumps(headers, indent=2)))
            print('http status :', r.status_code)
            print(method, r.url)
            if payload:
                print("DATA", json.dumps(payload))

        try:
            r.raise_for_status()
        except:
            raise SourceException(
                r.status_code,
                -1,
                '%s:\n %s' % (r.url, 'Error Occured'),
                headers=r.headers)
        finally:
            r.connection.close()

        if r.text and len(r.text) > 0 and r.text != 'null':

            results = r.json() if return_json else r.text.strip()
            if self.trace:  # pragma: no cover
                if return_json:
                    print('RESP', results)
                    print()
            return results
        else:
            return None

    def _get(self, url, args=None, payload=None, is_json=False, **kwargs):
        if args:
            kwargs.update(args)
        return self._internal_call('GET', url, is_json, payload, kwargs)

    def _post(self, url, args=None, payload=None, is_json=False, **kwargs):
        if args:
            kwargs.update(args)
        return self._internal_call('POST', url, is_json, payload, kwargs)

    def _delete(self, url, args=None, payload=None, is_json=False, **kwargs):
        if args:
            kwargs.update(args)
        return self._internal_call('DELETE', url, is_json, payload, kwargs)

    def _put(self, url, args=None, payload=None, is_json=False, **kwargs):
        if args:
            kwargs.update(args)
        return self._internal_call('PUT', url, is_json, payload, kwargs)


#Music Source Classes#
#----------------------------------------------


class chiasenhac_vn(BaseSourceScrapper):

    _PREFIX = 'http://chiasenhac.vn/'
    _NAME = 'chiasenhac.vm'
    _S_URL = "https://chiasenhac.vn/tim-kiem"
    _HEADERS = {
        'Host':
        'chiasenhac.vn',
        'Connection':
        'keep-alive',
        'User-Agent':
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36',
        'Accept':
        'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding':
        'gzip, deflate',
        'Accept-Language':
        'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7'
    }

    _MAX_SEARCH_PAGE_RESULT = 10  #Maximum no. of results in search page of chiasenhac.vm
    _MAX_SEARCH = _MAX_SEARCH_PAGE_RESULT
    _M4A_32_STR = 'M4A 32kbps'

    class Quality(Enum):
        flac = 'Lossless'
        m4a_500kbps = '500kbps'
        mp3_320kbps = '320kbps'
        mp3_128kbps = '128kbps'
        m4a_32kbps = '32kbps'

    def __init__(self,
                 requests_session=None,
                 trace=False,
                 trace_out=False,
                 proxies=None,
                 requests_timeout=None):
        super().__init__(self._PREFIX, self._HEADERS, self._NAME, trace,
                         trace_out, requests_session, proxies,
                         requests_timeout)

    @staticmethod
    def _is_download_a(tag):
        # return tag.name == 'a' and tag.has_attr(
        #     'title') and 'Click' in tag['title']
        return tag.name == 'a' and tag.has_attr('class') and tag['class'] == "download_item"

    @staticmethod
    def _scrap_search(html, max=None):

        if not max:
            max = chiasenhac_vn._MAX_SEARCH_PAGE_RESULT

        soup = bs(html, 'html5lib')

        songs_div = soup.find('div',attrs={'id':'nav-music'})

        if songs_div:
            for i, song_li in enumerate(songs_div.find_all('li')):
                if i <= max:
                    song_name = None
                    song_artist = None
                    song_url = None

                    song_name_h5 = song_li.find('h5')
                    if song_name_h5:
                        song_name = song_name_h5.string

                        song_a = song_name_h5.find('a')
                        if song_a:
                            song_url = song_a['href']
                    else:
                        max = max + 1
                        continue
                    
                    song_artist_div = song_li.find('div', attrs={'class':'author'})
                    if song_artist_div:
                        song_artist = song_artist_div.string

                    
                    yield (song_name, song_artist, song_url)

    @staticmethod
    def _scrap_download_details(html):
        soup = bs(html, 'html5lib')
        download_data = []

        #Download links anchor tag
        # a_downloads = soup.find_all(chiasenhac_vn._is_download_a)
        a_downloads = soup.find_all('a', class_="download_item")

        for a_download in a_downloads:
            size = None
            quality = None
            if 'href' in a_download.attrs.keys():
                d_url = a_download['href']
            else:
                d_url = None

            data = [line for line in get_inner_texts(a_download)]

            if len(data) == 2 and chiasenhac_vn._M4A_32_STR in data[1]:
                size = data[1].split(chiasenhac_vn._M4A_32_STR)[1].strip()
                quality = chiasenhac_vn.Quality.m4a_32kbps

            elif len(data) == 4:
                size = data[3].strip()
                # quality = QUALITY_DICT[data[1].strip()]
                # quality = tuple(q for q in Quality if q.value == data[1].strip)[0]
                for q in chiasenhac_vn.Quality:
                    if q.value in data[2].strip():
                        quality = q

            file_data = (quality, d_url, size)
            download_data.append(file_data)
        return download_data

    @staticmethod
    def _scrap_song_info(html):
        #initiliaze the variables
        song_name = None
        artist = None
        album = None
        year = None
        lyrics = []

        soup = bs(html, 'html5lib')

        div_lyric = soup.find('div', attrs={"id": "fulllyric"})
        div_songinfo = soup.find('div', attrs={"id": "pills-plus"})

        #For Song Name
        div_h4 = div_songinfo.find('h4')
        if div_h4:
            span_songname = div_h4.find('span')
            if span_songname:
                song_name = span_songname.string.strip()

        for i, tag in enumerate(div_songinfo.find_all('li')):
            if i == 0:
                try:
                    artist = tag.find(a).string
                except:
                    pass
            elif i == 1:
                try:
                    album = tag.find(a).string
                except:
                    pass
            elif i == 2:
                year = tag.string


        #For Lyrics
        if div_lyric:
            lyrics = tuple(line.strip() for line in get_inner_texts(div_lyric))

        return (song_name, artist, album, year, lyrics)

    @staticmethod
    def refresh_download_url(url, increment=True):
        """Tries to refresh the download url if it is changed.
           
           Args:
                url: Download url to refresh
                increment: if True then increase the base number.

           Download url from www.chiasenhac.vm are generally in
           form of:-
            http://data04.chiasenhac.com/downloads/../{num}/..mp3

           This {num} usually changes with time incremently.
           So increasing or decreasing this {num} can give us current 
           download url.
        """
        data = url.split('/')
        if not increment and int(data[5]) > 0:
            data[5] = str(int(data[5]) - 1)
        else:
            data[5] = str(int(data[5]) + 1)
        return '/'.join(data)

    @Cache.cache_constant()
    def get_search_url(self, html=None):
        """Return the current search url to use in POST
           requests for search queries."""

        if not html:
            html = self._get(self._PREFIX)
        soup = bs(html, 'html5lib')

        url = soup.find('form', attrs={'name': 'song_list'})['action']

        if url.endswith('?s='):
            url = url[:-3]
        # elif url.endswith('s='):
        #     url = url[:-2]
        # elif url.endswith('='):
        #     url = url[:-1]
        return url

    def _update_search_url(self, html=None):
        """Tries to update search url."""
        try:
            self._S_URL = self.get_search_url(html)
        except:
            pass

    def search(self, query, max=_MAX_SEARCH, json_serializable=False):
        """Search the query from music source.
           
           Search the given query from http://chiasenhac.vm
           and fetch the results upto 'max' arg.

           Args:
                query: A string to search. Ex:- Song name.
                max: (Optional) Maximum number of results
                     to retrive. It can take value upto 25 
                     [Default: 5]
                json_serializable: True or False
                    
           Returns:
                IF json_serializable=False [DEFAULT] :-
                    A generator object of tuples
                    For Example:-
                
                    ('Ride', 'My Artist', 'http://song.com')
                IF json_serializable=True :-
                    A list of dict with syntax:-
                    [{'song':'Ride', 'artist':'TwentyOnePilots', 'url':'http://abc.com'},
                     {'song':'Ride', 'artist':'TwentyOnePilots', 'url':'http://abc.com'}]


                If some of the value is not found then 'None' 
                is given.

                If some HttpError occurs such as Not Found 404
                then it will return the status_code of response
                object.
        """
        self._update_search_url()

        if not json_serializable:
            odd_num = max % self._MAX_SEARCH_PAGE_RESULT
            pages = max // self._MAX_SEARCH_PAGE_RESULT

            # if pages in  (0,1) :
            #     html = self._get(self._S_URL, s=query)
            #     return self._scrap_search(html, max)
            # else:
            #     html = self._get(self._S_URL, s=query, page=1)
            #     result = self._scrap_search(html)

            #     for page_num in range(2, pages+1):
            #         html = self._get(self._S_URL, s=query, page=page_num)
            #         result = chain(result, self._scrap_search(html))

            #     html = self._get(self._S_URL, s=query, page=pages+1)
            #     result = chain(result, self._scrap_search(html, max=odd_num))

            #     return result
            result = []
            for page_num in range(0, pages):
                html = self._get(self._S_URL, q=query, page_music=page_num + 1)
                result = chain(result, self._scrap_search(html))
            if odd_num:
                html = self._get(self._S_URL, q=query, page_music=pages + 1)
                return chain(result, self._scrap_search(html, max=odd_num))

            return result
        else:
            return [{
                'song': data[0],
                'artist': data[1],
                'url': data[2]
            } for data in self.search(query, max)]

    def download_details(self, url, json_serializable=False):
        """Scrap the download url and other details.

           Fetch the  quality, download url, size of song
           and returns them in a list of tuple [by Default].

           Args:
                url: Song url
                json_serializable: if True, then return is jsonizable

           Returns:
                IF json_serializable=False [DEFAULT] :-
                    It return the list of tuple containing download
                    info. Syntax:-
                    [(quality, download_url, size),
                    (quality, download_url, size)]

                    NOTE:- quality is of chiasenhac_vn.Quality type

                IF json_serializable=True :-
                    It return the list of dict containing download
                    info. Example:-
                    [{'quality':'Lossless', 'url':'http;//abc/', 'size':'2MB'},
                    {'quality':'500kbps', 'url':'http;//abd/', 'size':'1MB'}]
        """

        # html = self._get(url[:-5] + '_download.html')
        html = self._get(url)
        datas = self._scrap_download_details(html)

        if json_serializable:
            return [{
                'quality': data[0].value,
                'url': data[1],
                'size': data[2]
            } for data in datas]
        else:
            return datas

    def song_info(self, url, json_serializable=False):
        """Scrap the song details from given url.

           Retrives the song details such as name, artist
           album, year, lyrics from song url.

           Args:
                s_url: Url of the song
                json_serializable: if True, then return is jsonizable(a dict)

           Returns:
                IF json_serializable=False [DEFAULT] :-
                    It return the list containing song_name, artist, album, year,
                    lyrics in respective order.

                IF json_serializable=True :-
                    It return the list of dict containing download
                    info. Example:-
                    [{'name':'Ride', 'artist':'Coldplay', 'year':'2000', 'lyrics':'Lyrics'},
                    {'name':'Play', 'artist':'Coldplay', 'year':'2011', 'lyrics':'Lyrics'}]

                NOTE:- 
                Lyrics are list type having each line seperately.
         """

        if not json_serializable:
            html = self._get(url)
            return self._scrap_song_info(html)
        else:
            data = self.song_info(url)
            return {
                'name': data[0],
                'artist': data[1],
                'album': data[2],
                'year': data[3],
                'lyrics': data[4]
            }


#Register music sources( class which inherit 'BaseSource')
for name, class_type in inspect.getmembers(
        sys.modules[__name__],
        lambda member: inspect.isclass(member) and member.__module__ == __name__
):
    if not name == "BaseSourceScrapper":  #TODO: Replace this Hardcoded hotfix with
        source_class, *base_classes = inspect.getmro(
            class_type)  #      permanent fix.
        if BaseSource in base_classes:
            #update the dict
            SOURCES.update({name: source_class})

if not SOURCES:
    warnings.warn(_NO_SOURCE_WARNING)


#Returns the default source class
def get_default():
    return SOURCES[SRC_DEFAULT]


def get_source(name=None):
    if name == 'default':
        return get_default()
    else:
        try:
            return SOURCES[name]
        except KeyError:
            raise KeyError("No source named {} found.".format(name))
