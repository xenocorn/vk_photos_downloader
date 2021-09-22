import vk_api
import os
import time
from threading import Thread
from queue import Queue
import requests
from sys import argv


DOWNLOAD_DIR = "photos"
THREADS = 8
COUNT_PER_REQUEST = 190


def downloader(q):
    #print("Downloader thread start")
    while True:
        element = q.get()
        if element == "STOP":
            break
        path, url = element
        r = requests.get(url, allow_redirects=True)
        open(path, "wb").write(r.content)
        #print("downloaded", path)
    #print("Downloader thread stop")
    

def download_album(connection, album_id, title):
    total = 0
    album_path = DOWNLOAD_DIR + "/" + title
    if not os.path.exists(album_path):
        os.makedirs(album_path)
    count = COUNT_PER_REQUEST
    offset = 0
    resp = None
    while True:
        try:
            resp = connection.method('photos.get', {'album_id': album_id, 'count': count, 'offset': offset})
        except Exception as e:
            se = str(e)
            if "[29]" in se or "Rate limit reached" in se:
                print(("!"*20), "Rate limit reached", ("!"*20))
                time.sleep(360)
                continue
            raise e
        resp["count"] = len(resp["items"])
        if resp["count"] < 1:
            break
        offset += count
        total += resp["count"]
        print("received", resp["count"], "total", total)
        photos = resp["items"]
        time_to_sleep = 5
        q = Queue(count)
        threads = []
        for i in range(THREADS):
            thread = Thread(target = downloader, args = (q, ))
            threads.append(thread)
            thread.start()
        downloading_start = time.time()
        for photo in photos:
            url = None
            height = 0
            for size in photo["sizes"]:
                if size["height"] > height:
                    url = size["url"]
            fmt = ".jpg"
            if ".png" in url.lower():
                fmt = ".png"
            elif ".jpeg" in url.lower():
                fmt = ".jpeg"
            path = album_path+"/"+str(photo["id"])+fmt
            q.put((path, url))
        for _ in threads:
            q.put("STOP")
        for t in threads:
            t.join()
        downloading_stop = time.time()
        downloading_time = downloading_stop - downloading_start
        print("downloading_time", downloading_time)
        if downloading_time < time_to_sleep:
            time.sleep(time_to_sleep - downloading_time)
    return total

def main():
    LOGIN = argv[1]
    PASSWORD = argv[2]
    connection = vk_api.VkApi(login=LOGIN, password=PASSWORD)
    connection.auth()
    ex = None
    total = 0
    start_time = time.time()
    resp = connection.method('photos.getAlbums', {'count': 1000, 'need_system': 1})
    print("Donloading albums:")
    for item in resp['items']:
        item["title"] = item["title"].replace(" ", "_") + "_" + str(item["id"])
        print(item["title"])
        total += download_album(connection, item["id"], item["title"])
    end_time = time.time()
    print(("-"*40),"END",("-"*40))
    print("time: ", end_time-start_time)

if __name__ ==  "__main__":
    main()
