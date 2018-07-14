

import time
start_time  = time.time()


from MusicSource import MusicSource



source = MusicSource.SOURCES['chiasenhac_vn']()

print(source.download_details("http://m2.chiasenhac.vn/mp3/us-uk/us-rap-hiphop/ride~twenty-one-pilots~ts3v0rszq2na41.html"))





print("-------{} seconds taken--------".format(time.time()-start_time))

# import requests

# res = requests.get('http://google.com')

# js = res.json()

# print(js)