#Imports
import requests
from bs4 import BeautifulSoup as bs, element, NavigableString

import os
import ntpath
import datetime
import json
from subprocess import check_call, DEVNULL, STDOUT

from spotipy import oauth2, SpotifyException


   
def remote_file_size(url, unit='B'):
    """Get the file size using HEAD request.

       Fetch remote http file size by sending
       http head request to server.

       Args:
            url: File url
            unit: Unit of return('B' for bytes,
                                 'MB' for mb,
                                 'KB' for kb,
                                 'GB' for gb)
       
       Returns:
            Size of file upto 2 decimal places.

            If some HttpError occurs such as 404, 500
            then it returns None

            If the HEAD response does not have
            'Content-Length' header then returns 0
    """

    unit = unit.upper()
    content_key = ('Content-Length','content-length')
    res = requests.head(url)

    if not res.status_code == 200:           
        return None

    if content_key[0] in res.headers.keys():
        size = int(res.headers[content_key[0]].strip())
    elif content_key[1] in res.headers.keys():
        size = int(res.headers[content_key[0]].strip())
    else:
        return 0
        
    if unit == 'B':
        return size
    else:
        return convert_size(size, unit)
    return size


def get_inner_texts(tag):
    """Retrives the text inside a tag

       Fetch the string/NavigableString inside the 
       provided tag.

       Args:
            tag: An beautifulsoup4 tag to look inside.

       Returns:
            A generator object of strings.
    """
    # return (line for line in tag.children 
    #             if isinstance(line, (str, NavigableString)))

    # return (line if isinstance(line,NavigableString) 
    #                 else '\n'.join(_get_inner_texts(line)) for line in tag.children)
    for child in tag.children:
        if isinstance(child, NavigableString):
            yield child
        elif isinstance(child,element.Tag):
            for line in get_inner_texts(child):
                yield line


def unit_to_bytes(in_unit, size):
    """Returns the 'size' in bytes

       Args:
            in_unit: Unit of input data.
                     Supported input ('kb', 'mb', 'gb')
            size: Input size in int or float

       Returns:
            Size in bytes [float/int]
    """
    in_unit = in_unit.lower()

    if in_unit == 'kb':
        size = size * 1024
    elif in_unit == 'mb':
        size = size*(1024**2)
    elif in_unit == 'gb':
        size = size*(1024**3)
    return size


def convert_size(size,  unit='mb', dec=2):
    """Convert the given unit into other.

       Args:
            size: Size to convert.
                  Example:-
                  "2.4 mb", "22 KB", "1.9 gb"

                  For 'bytes' only int is sufficient:
                  Example:-
                  1445, 112788
            
            unit: Unit to convert to.

            dec: No. of decimal place in return

       Returns:
            Returns int/float

    """
    try:
        unit = unit.lower()
    except AttributeError:
        raise TypeError("'unit' args must be a valid string.")

    if isinstance(size, str):   
        in_unit = ''.join(s for s in size.lower() if str.isalpha(s))
        size = float(''.join(s for s in size if not str.isalpha(s)))
    elif isinstance(size, (int, float)):
        in_unit = 'bytes'

    if in_unit == unit:
        return size
    else:
        size = unit_to_bytes(in_unit, size)

    if unit == 'kb':
        size = round(size/(1024**1), dec)
    elif unit == 'mb':
        size = round(size/(1024**2), dec)
    elif unit == 'gb':
        size = round(size/(1024**3), dec)
    
    return size


def is_online():
    """Returns True if devices can communicate on internet.
    """
    for time_out in (2,5,10,15):
        try:
            # connect to the host -- tells us if the host is actually
            # reachable
            s = requests.adapters.socket.create_connection(("www.google.com", 80), time_out)
            s.close()
            return True
        except OSError:
            pass
    return False


def prompt_for_spotify_token(username, scope, client_id = None,
        client_secret = None, redirect_uri = None):
    ''' prompts the user to login if necessary and returns
        the user token suitable for use with the spotipy.Spotify 
        constructor

        Parameters:

         - username - the Spotify username
         - scope - the desired scope of the request
         - client_id - the client id of your app
         - client_secret - the client secret of your app
         - redirect_uri - the redirect URI of your app

    '''
    #NOTE:-
    #Modified prompt_for_user_token() from util.py in spotipy.
    #Only difference is change in webbrowser calling. It redirect
    #the standard output to dev/null so that terminal does not get
    #filled with gtk warnings and other.

    if not client_id:
        client_id = os.getenv('SPOTIPY_CLIENT_ID')

    if not client_secret:
        client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')

    if not redirect_uri:
        redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')

    if not client_id:
        print('''
            You need to set your Spotify API credentials. You can do this by
            setting environment variables like so:

            export SPOTIPY_CLIENT_ID='your-spotify-client-id'
            export SPOTIPY_CLIENT_SECRET='your-spotify-client-secret'
            export SPOTIPY_REDIRECT_URI='your-app-redirect-url'

            Get your credentials at     
                https://developer.spotify.com/my-applications
        ''')
        raise SpotifyException(550, -1, 'no credentials set')

    sp_oauth = oauth2.SpotifyOAuth(client_id, client_secret, redirect_uri, 
        scope=scope, cache_path=".cache-" + username )

    # try to get a valid token for this user, from the cache,
    # if not in the cache, the create a new (this will send
    # the user to a web page where they can authorize this app)

    token_info = sp_oauth.get_cached_token()

    if not token_info:
        print('''

            User authentication requires interaction with your
            web browser. Once you enter your credentials and
            give authorization, you will be redirected to
            a url.  Paste that url you were directed to to
            complete the authorization.

        ''')
        auth_url = sp_oauth.get_authorize_url()
        try:
            check_call(('python','-m','webbrowser','-t',auth_url), stdout=DEVNULL, stderr=STDOUT)
            print("Opened %s in your browser" % auth_url)
        except:
            print("Please navigate here: %s" % auth_url)

        print()
        print()
        try:
            response = raw_input("Enter the URL you were redirected to: ")
        except NameError:
            response = input("Enter the URL you were redirected to: ")

        print()
        print() 

        code = sp_oauth.parse_response_code(response)
        token_info = sp_oauth.get_access_token(code)
    # Auth'ed API request
    if token_info:
        return token_info['access_token']
    else:
        return None



def get_quality(all_qualities, pref=0, *args):
    """Gets the best, middle or lowest quality from
       the Quality types given.

       Args:
            all_quality: iterable having all qualities 
                         from best to lowest 
            *args: qualities to sort
            pref: (0,1,2) int
                  0 => Best
                  1 => Middle
                  2 => Lowest
    """
    #Remove duplicate entries
    args = list(dict.fromkeys(args))

    #make local copy of Qualities
    q_list = tuple(q for q in all_qualities)
    sorted_q = []

    for q in q_list:
        for given_q in args:
            if q == given_q:
                sorted_q.append(q)

    lth = len(sorted_q)
    if pref == 0:
        return sorted_q[0]
        
    elif pref == 1:
        lth = len(sorted_q)
        if is_even(lth):
            return sorted_q[lth//2]
        else:
            return sorted_q[(lth+1)//2]

    elif pref == 2:
        return sorted_q[lth-1]


class Cache:
    """Very Simple Class for implementing caching."""

    CACHE_DIR = os.path.join(ntpath.dirname(__file__), '.cache/')
    CACHE_EXT = '.cache'

    @staticmethod
    def is_cache_expired(time_cache):
        """Return True is cache is expired.
           
           Args:
                time_cache: A datetime object or timestamp
                            of cache expire time."""
        try:
            if not isinstance(time_cache, datetime.datetime):
                time_cache = datetime.datetime.fromtimestamp(time_cache)
            return datetime.datetime.now() > time_cache
        except TypeError:
            return True


    @staticmethod
    def _write_cache(path, data, expire):
        create_file(path)
        with open(path,'w') as fw:
            expire = datetime.datetime.now() + datetime.timedelta(hours=expire)
            data = {'expire': expire.timestamp(), 'content': data}
            json.dump(data,fw)


    @staticmethod
    def _read_cache(path):
        try:
            with open(path,'r') as fr:
                data = json.load(fr)
            if not 'expire' in data.keys() and 'content' in data.keys():
                return None
            else:
                return data
        except json.JSONDecodeError:
            return None


    @classmethod
    def cache_constant(cls, path=None, expire=24):
        """Cache the results of function in json format in
           external file.
           NOTE:- Apply only on functions whose return is not depended 
                  upon its arguments.

           Args:
                path: Full path where cache file will be stored.
                expire: Hours after which cache expire.
           """
        def decorater(func):

            cache_path = path
            if not cache_path:
                cache_path = cls.CACHE_DIR + func.__name__ + cls.CACHE_EXT
            

            def wrapper(*args, **kwargs):
                
                create_file(cache_path)

                cache_data = cls._read_cache(cache_path)
                if cache_data:
                    if not cls.is_cache_expired(cache_data['expire']):
                        return cache_data['content']
                    
                data = func(*args, **kwargs)
                cls._write_cache(cache_path, data, expire)
                return data

            return wrapper
        return decorater
                















