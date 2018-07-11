import requests

from bs4 import BeautifulSoup as bs, element, NavigableString





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

            


  


    


