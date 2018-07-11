import requests

from bs4 import BeautifulSoup as bs, element, NavigableString

try:
    from MusicSource.Song import  Quality
    from MusicSource.utility import get_inner_texts, convert_size
except ModuleNotFoundError:
    from Song import Quality
    from utility import get_inner_texts, convert_size





class _chiasenhac_vm():
    """This class provide methods for scrapping chiasenhac.vm"""

    HEADER = {
        'Host': 'chiasenhac.vn',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7'   
    }

    S_HOST = 'search.chiasenhac.vn'
    S_URL = "http://search.chiasenhac.vn/search.php"
    M4A_32_STR = 'Mobile Download: M4A 32kbps'


    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update(self.HEADER)


    @staticmethod
    def _is_download_a(tag):
        return tag.name == 'a' and tag.has_attr('title') and 'Click' in tag['title']



    def _search(self, host, query, max):

        query = {'s' : query}
        response = self.s.get(self.S_URL, params=query, headers = {'Host': host})

        if not response.status_code == 200:
            return response.status_code

        html = response.text.strip()
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
                            # if col[0] == 0:                    ##Deprected because first
                            #     index = int(col[1].p.string)   ## <td> is not always int
                                
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



    def _song_info(self, s_url):
        
        #initiliaze the variables
        song_name = None
        artist = None
        album = None
        year = None
        lyrics = []


        response = self.s.get(s_url)
        if not response.status_code == 200:
            return response.status_code

        html = response.text.strip()
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



    def _download_info(self, url):
        """Scrap the download url and other details.

           Fetch the  quality, download url, size of song
           and returns them in a list of tuple.

           Args:
                url: Song url

           Returns:
                It return the list of tuple containing download
                info. Syntax:-
                [(quality, download_url, size),
                 (quality, download_url, size)]

                NOTE:-
                quality is in Enum type."""


        if isinstance(url,str):
            url = "{}_{}".format(url[:-5],"download.html")
        else:
            raise TypeError("'url must be a valid string.'")

        
        response = self.s.get(url)
        if not response.status_code == 200:
            return response.status_code

        html = response.text.strip()
        soup = bs(html, 'html5lib')

        download_data = []

        #Download links anchor tag
        a_downloads = soup.find_all(self._is_download_a)

        for a_download in a_downloads:
            size = None
            quality = None

            if 'href' in a_download.attrs.keys():
                d_url = a_download['href']
            else:
                d_url = None

            data = [line for line in get_inner_texts(a_download)]

            if len(data) == 1 and self.M4A_32_STR in data[0] : 
                size = data[0][len(self.M4A_32_STR):].strip()
                quality = Quality.m4a_32kbps

            elif len(data) == 3:
                size = data[2].strip()
                # quality = QUALITY_DICT[data[1].strip()]
                # quality = tuple(q for q in Quality if q.value == data[1].strip)[0]
                for q in Quality:
                    if q.value == data[1].strip():
                        quality = q
                              

            file_data = (quality, d_url, size)
            
            download_data.append(file_data)
        
            
        return download_data
        


    @staticmethod
    def refresh_download_url(url, increment=True):
        
        data = url.split('/')
        
        if not increment and int(data[5]) > 0:
            data[5] = str(int(data[5]) - 1)
        else:
            data[5] = str(int(data[5]) + 1)

        return '/'.join(data)




    def search(self, query, max=5):
        """Search the query from music source.
           
           Search the given query from http://chiasenhac.vm
           and fetch the results upto 'max' arg.

           Args:
                query: A string to search. Ex:- Song name.
                max: (Optional) Maximum number of results
                     to retrive. It can take value upto 25 
                     [Default: 5]
                    
           Returns:
                A generator object of tuples
                For Example:-
            
                ('Ride', 'My Artist', 'http://song.com')

                If some of the value is not found then 'None' 
                is given.

                If some HttpError occurs such as Not Found 404
                then it will return the status_code of response
                object.
            """

        return self._search(self.S_HOST, query, max)


        
    def song_info(self, s_url):
        """Scrap the song details from given url.

           Retrives the song details such as name, artist
           album, year, lyrics from song url.

           Args:
                s_url: Url of the song

           Returns:
                A list having song_name, artist, album, year,
                lyrics in respective order.
                NOTE:- 
                Lyrics are list type having each line seperately. """
        
        return self._song_info(s_url)

    

    def download_info(self, url=None, query=None):
        """Scrap the download url and other details.

           Fetch the  quality, download url, size of song
           and returns them in a list of tuple.

           Args:
                url: Song url
                query: Key words about song. It will be used 
                       to get top search result.

                NOTE:-
                Only one of them is required. If both of them
                given then 'url' will be considered.

           Returns:
                It return the list of tuple containing download
                info. Syntax:-
                [(quality, download_url, size),
                 (quality, download_url, size)]

                NOTE:-
                quality is in Enum type.     
        """


        if url:
            return self._download_info(url)
        elif query:
            return self._download_info(tuple(self.search(query, max=1))[0][2])
        else:
            raise Exception("No args were given")




    




def new():
    """Returns a chiasenhac_vm object."""
    return _chiasenhac_vm()
