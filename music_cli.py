from MusicSource import chiasenhac_vn
from MusicSource.Song import Quality

import time
start_time  = time.time()

src = chiasenhac_vn.new()



print(src.download_info(query = 'Voilent Hill Coldplay'))



print("-------{} seconds taken--------".format(time.time()-start_time))