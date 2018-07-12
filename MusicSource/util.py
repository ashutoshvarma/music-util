#Imports
import requests
from bs4 import BeautifulSoup as bs, element, NavigableString

import os
from subprocess import check_call, DEVNULL, STDOUT

from spotipy import oauth2, SpotifyException

try:
    from MusicSource.Song import  Quality
except ModuleNotFoundError:
    from Song import Quality
    



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


def is_even(x):
    """Returns True if even."""
    return x & 1


def get_quality( *args, pref=0):
    """Gets the best, middle or lowest quality from
       the Quality types given.

       Args:
            *args: Quality types
            pref: (0,1,2) int
                  0 => Best
                  1 => Middle
                  2 => Lowest
    """
    #Remove duplicate entries
    args = list(dict.fromkeys(args))

    #make local copy of Qualities
    q_list = tuple(q for q in Quality)
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



    


