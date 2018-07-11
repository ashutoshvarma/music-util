from dataclasses import dataclass
from enum import Enum



class Quality(Enum):
    flac = 'Lossless'
    m4a_32kbps = 'M4A 32kbps'
    mp3_128kbps = '128kbps'
    mp3_320kbps = '320kbps'
    m4a_500kbps = '500kbps'



class SongFile(object):

    def __init__(self, *args):
        for lst in args:
            self.add(*lst)

    
    def add(self, quality, url, size=None):
        setattr(self, quality.name, (url, size))


    def __iter__(self):
        for attr, value in self.__dict__.items():
            attr = tuple(q for q in Quality if q.name==attr)[0]
            yield attr, value[0], value[1]


    def __delitem__(self, key):
        del self.__dict__[key]


    def types(self):
        return (pair[0] for pair in self.__iter__())

    def urls(self):
        return (pair[1][0] for pair in self.__iter__())

    

@dataclass
class Song:
    """An object to store song details."""

    name: str 
    artist: str
    album: str = None
    year: int = None
    lyrics: tuple = None
    file: SongFile = SongFile()

    def __str__(self):
        return '{self.name} - {self.artist}'.format(self=self)


    def __setitem__(self, attr, value):
        if not attr == 'file':
            self.__dict__[attr] = value
        else:
            raise AttributeError("can't set attribute '{}'".format(attr))


    def __setattr__(self, attr, value):
        if attr == 'file':
            if not isinstance(value, SongFile):
                raise AttributeError("can't set attribute '{}'".format(attr))

        self.__dict__[attr] = value







    









