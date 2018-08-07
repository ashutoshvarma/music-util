#Imports
import os,sys
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
    """Base class for all music sources."""

    def __init__(self, prefix, header, name="", trace=False, trace_out=False, 
                requests_session = None, proxies=None, requests_timeout=None):
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

        r = self._session.request(method, url, headers=headers,
                                  proxies=self.proxies, **args)

        if self.trace_out:
            print("Base url :",url)

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
            raise SourceException(r.status_code,
                -1, '%s:\n %s' % (r.url, 'Error Occured'), headers=r.headers)
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

class chiasenhac_vn(BaseSource):
    
    _PREFIX = 'http://chiasenhac.vn/'
    _NAME = 'chiasenhac.vm'
    _S_URL = "http://search2.chiase-nhac.vn/search.php"
    _HEADERS = {
        'Host': 'chiasenhac.vn',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7'   
    }

    _MAX_SEARCH_PAGE_RESULT = 25                    #Maximum no. of results in search page of chiasenhac.vm
    _MAX_SEARCH = _MAX_SEARCH_PAGE_RESULT
    _M4A_32_STR = 'Mobile Download: M4A 32kbps'


    class Quality(Enum):
        flac = 'Lossless'
        m4a_500kbps = '500kbps'
        mp3_320kbps = '320kbps'
        mp3_128kbps = '128kbps'
        m4a_32kbps = 'M4A 32kbps'


    def __init__(self, requests_session=None, trace=False, trace_out=False,
                 proxies=None, requests_timeout=None):
        super().__init__(self._PREFIX, self._HEADERS, self._NAME, trace,
                         trace_out, requests_session, proxies, requests_timeout)


    @staticmethod
    def _is_download_a(tag):
        return tag.name == 'a' and tag.has_attr('title') and 'Click' in tag['title']


    @staticmethod
    def _scrap_search(html, max=None):

        if not max:
            max = chiasenhac_vn._MAX_SEARCH_PAGE_RESULT

        soup = bs(html, 'html5lib')

        table_search = soup.find('table', attrs={'class':'tbtable'})

        if table_search:
            for rows in enumerate(table_search.find_all('tr')):
                if rows[0] <= max and not rows[0] == 0:     #Escaping header row
                    song_name = None
                    artist = None
                    song_url = None

                    if not rows[0] == 0:    #Escaping header row
                        for col in enumerate(rows[1].find_all('td')):
                            # if col[0] == 0:                   ##Deprected because first
                            #     index = int(col[1].p.string)  ## <td> is not always int                              
                            if col[0] == 1:
                                #Gets the <a href> tag
                                song_a = col[1].find('a')                             
                                if song_a:
                                    p_artist = song_a.find_next('p')
                                    song_name = song_a.string                                  
                                    #Gets the content of 'href'
                                    #attribute
                                    if 'href' in song_a.attrs.keys():
                                        song_url = song_a['href']
                                    if p_artist:
                                        artist = p_artist.string
                        # song_data = dict(song=song, artist=artist, url=song_url)
                        # search_data.insert(rows[0], song_data)
                    yield (song_name, artist, song_url)


    @staticmethod
    def _scrap_download_details(html):
        soup = bs(html, 'html5lib')
        download_data = []

        #Download links anchor tag
        a_downloads = soup.find_all(chiasenhac_vn._is_download_a)

        for a_download in a_downloads:
            size = None
            quality = None
            if 'href' in a_download.attrs.keys():
                d_url = a_download['href']
            else:
                d_url = None

            data = [line for line in get_inner_texts(a_download)]

            if len(data) == 1 and chiasenhac_vn._M4A_32_STR in data[0] : 
                size = data[0][len(chiasenhac_vn._M4A_32_STR):].strip()
                quality = chiasenhac_vn.Quality.m4a_32kbps

            elif len(data) == 3:
                size = data[2].strip()
                # quality = QUALITY_DICT[data[1].strip()]
                # quality = tuple(q for q in Quality if q.value == data[1].strip)[0]
                for q in chiasenhac_vn.Quality:
                    if q.value == data[1].strip():
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
    
        div_songinfo = soup.find('div' ,attrs={"id":"fulllyric"})

        #For Song Name
        a_song_name = div_songinfo.find('strong').a
        if a_song_name:
            song_name = a_song_name.string.strip()

        #For Other Info(Artist, Album, Year)
        for i,tag in enumerate(div_songinfo.find_all('b')):
            if i == 0:
                artist = tag.string
            elif i == 1:
                album = tag.a.string
            elif i == 2:
                year = tag.string

        #For Lyrics
        p_lyrics = div_songinfo.find('p',attrs={"class":"genmed"})
        if p_lyrics:
            lyrics = tuple(line.strip() for line in get_inner_texts(p_lyrics))

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

        url = soup.find('form', attrs={'name':'song_list'})['action']

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

            if pages == 0:
                html = self._get(self._S_URL, s=query)
                return self._scrap_search(html, max)
            else:
                html = self._get(self._S_URL, s=query, page=1)
                result = self._scrap_search(html)

                for page_num in range(2, pages+1):
                    html = self._get(self._S_URL, s=query, page=page_num)
                    result = chain(result, self._scrap_search(html))

                html = self._get(self._S_URL, s=query, page=pages+1)
                result = chain(result, self._scrap_search(html, max=odd_num))

                return result
        else:
            return [ {'song':data[0], 'artist':data[1], 'url':data[2]} for data in self.search(query, max)]


    def download_details(self,url, json_serializable=False):
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

        html = self._get(url[:-5] + '_download.html')
        datas =  self._scrap_download_details(html)

        if json_serializable:
            return [{'quality':data[0].value ,'url':data[1], 'size':data[2]} for data in datas]
        else:
            return datas
            

    def song_info(self,url):
        """Scrap the song details from given url.

           Retrives the song details such as name, artist
           album, year, lyrics from song url.

           Args:
                s_url: Url of the song

           Returns:
                A list having song_name, artist, album, year,
                lyrics in respective order.
                NOTE:- 
                Lyrics are list type having each line seperately.
         """
        html = self._get(url)
        return self._scrap_song_info(html)





#Register music sources( class which inherit 'BaseSource')
for name, class_type in inspect.getmembers(sys.modules[__name__], 
        lambda member: inspect.isclass(member) and member.__module__ == __name__):

    source_class, *base_classes = inspect.getmro(class_type)
    if BaseSource in base_classes:
        #update the dict 
        SOURCES.update({name:source_class})

if not SOURCES:
    warnings.warn(_NO_SOURCE_WARNING)



#Returns the default source class
def get_default():
    return SOURCES[SRC_DEFAULT]

def get_source(name=None):
    try:
        return SOURCES[name]
    except KeyError:
        raise KeyError("No source named {} found.".format(name))


