#encoding: utf-8
import os, io
import shutil
import time
import json
import urllib, urllib2, zipfile


try:
    from renpy.exports import invoke_in_thread, restart_interaction
    from renpy.game import persistent
except:
    # Чтобы тестить на пеке
    import threading
    # Export to renpy
    def invoke_in_thread(fn, *args, **kwargs):
        def run():
            try:
                fn(*args, **kwargs)
            except:
                import traceback
                traceback.print_exc()

        t = threading.Thread(target=run)
        t.daemon = True
        t.start()
        
    class O():
        pass
    persistent = O()
    persistent.__dict__['download'] = O()
    persistent.download.loaded_size = 0
    restart_interaction = lambda : None

###################### Vars
host_url = 'http://191.ru/es/'
json_url = host_url + 'project2.json'
files_path = os.environ.get("ANDROID_PUBLIC", os.getcwd()) + '/'
print("Files_path:" + files_path)
temp_folder = files_path + "downloads/"
Mb = 1024*1024
block_sizes = [Mb, 5*Mb, 10*Mb, 20*Mb, 50*Mb]
BLOCK_SIZE = block_sizes[1]

##############################################################
##########              Кусочек локальных модов
##############################################################
class LocalMod(object):
    def __init__(self, path, files, **data):
        self.path = path
        self.files = files
        self.__dict__.update(data)

    @staticmethod
    def Create(path, files, **data):
        self = LocalMod(path, files=files, **data)
        self.enabled = True
        self.save()
        return self

    @staticmethod
    def Load(path):
        filepath = os.path.join(path,'mod.json')
        self = LocalMod(**json.load(open(filepath, 'r')))
        return self

    @staticmethod
    def LoadAll(root):
        mods = {}
        for path, dirs, files in os.walk(os.path.abspath(root)):
            if 'mod.json' in files:
                mod = LocalMod.Load(path)
                mods[mod.idmod] = mod
        return mods
    
    def save(self):
        filepath = os.path.join(self.path,'mod.json')
        json.dump(self.__dict__, open(filepath, 'w'))
        
    def delete(self):
        shutil.rmtree(self.path,True)
        for f in reversed(self.files):
            try:
                if f.endswith('.rpy') and (f + 'c' not in self.files):
                    os.remove(f + 'c')
                if os.path.isdir(f):
                    shutil.rmtree(f,True)
                else:
                    os.remove(f)
            except:
                pass
    



class Downloading(object):
    url = ''
    zip_file = ''
    loaded_size = 0
    file_size = 0
    files = []


    @property
    def progress(self):
        return mlobj.progress

    @progress.setter
    def progress(self, value):
        mlobj.progress = value

    def __init__(self, url='', **mod_data):
        self.mod_data = mod_data
        self.url = url
        if not url:
            return
        self.zip_file = temp_folder + url.split('/')[-1]
        if os.path.exists(self.zip_file):
            # Типа отрезаем последний кусок
            self.loaded_size = os.path.getsize(self.zip_file)
            if self.loaded_size < 0:
                self.loaded_size = 0
        else:
            open(self.zip_file, 'wb').close()

    def process(self):
        for _ in range(3):
            try:
                self.download()
                break
            except Exception as exp:
                print(exp)
            raise Exception(u'Ошибка загрузки')
        if not self.unpacking():
            return
        localmod = LocalMod.Create(self.files[0], self.files, **self.mod_data)
        self.progress = u'Готово'
        return localmod.idmod, localmod

    def download(self):
        fp_headers = urllib2.urlopen(self.url).headers
        # Значения
        self.file_size = float(fp_headers['content-length'])
        self.mod_data['size'] = float(fp_headers['content-length'])/Mb
        self.mod_data['last_modified'] = time.mktime(time.strptime(fp_headers['Last-Modified'], "%a, %d %b %Y %H:%M:%S %Z"))
        
        if self.file_size == self.loaded_size:
            self.progress = u'Загружено, ожидаем распаковку'
            return
        request = urllib2.Request(self.url, headers={'Range':'bytes=%d-' % self.loaded_size})
        with open(self.zip_file, 'r+b') as filestream:
            filestream.seek(self.loaded_size)

            self.progress = u'Загрузка: 0/%.2f Mb' % (self.file_size/Mb)
            fp = urllib2.urlopen(request)
            readed = fp.read(BLOCK_SIZE)
            while readed:
                filestream.write(readed)
                readed = fp.read(BLOCK_SIZE)
                self.loaded_size += BLOCK_SIZE
                self.progress = u'Загрузка: %d/%.2f Mb' % (self.loaded_size/Mb, self.file_size/Mb)
                #print(self.progress)
            self.progress = u'Загружено, ожидаем распаковку'

    def unpacking(self):
        self.progress = u'Распаковка...'
        try:
            zipf = zipfile.ZipFile(self.zip_file)
            self.files = []
            ln = len(zipf.namelist())
            for i, name in enumerate(zipf.namelist()):
                zipf.extract(name, files_path)
                self.progress = u'Распаковка : %d/%d' % (i, ln)
                #print(self.progress)
                os.rename(files_path+name, files_path+name.decode('cp866')) # Вроде так нежно декодить, такое себе
                self.files.append(files_path+name.decode('cp866'))
            try:
                os.remove(self.zip_file)
            except:
                pass
            self.progress = u"Распаковано"
            return True
        except Exception as exp:
            print(exp)
            self.progress = u'Ошибка распаковки'
            
    def __eq__(self, b):
        if self and b:
            return self.__dict__ == b.__dict__
        else:
            return False











##############################################################
##########              Кусочек модлоадера
##############################################################
#TODO: header Range
class ModLoader(object):
    __progress = u'Загрузка не ведется'  # Текущий прогресс
    processing = False
    connected = False  # Получилось ли загрузить индекс
    mods_on_page = 10
    sorting_func = lambda self, x: x['idmod']
    
    mods = {}
    sorted_mods = []
    pages = 0
    local_mods = {}

    @property
    def progress(self):
        return self.__progress

    @progress.setter
    def progress(self, value):
        print(value)
        self.__progress = value
        restart_interaction()


    def __init__(self):
        self.load_mods_index()
        self.local_mods = LocalMod.LoadAll(files_path)
        # Создание папки
        try:
            os.mkdir(temp_folder)
        except: pass
        # Прописываение в персистент
        if persistent.download == None:
            persistent.download = Downloading()
        self.download = persistent.download
        if self.download.loaded_size > 0:
            self.progress = u'Существет недокачаный файл!'


    def drop_mods(self):
        json.dump(self.mods, open('mods.json', 'w'))

    def load_mods_index(self):
        try:
            last_mod = time.mktime(time.strptime(urllib2.urlopen(json_url).headers['Last-Modified'], "%a, %d %b %Y %H:%M:%S %Z"))
            self.connected = True
            if not (os.path.exists('project2.json') and last_mod < os.path.getmtime('project2.json')):
                print(u"Download pleeeeease...")
                urllib.urlretrieve(json_url, 'project2.json')
        except Exception as e:
            print(u'Не удалось подключиться к серверу ' + str(e))
        
        try:
            js = json.load(io.open('project2.json', 'r', encoding='utf-8'))
            self.mods = {int(x['idmod']): {'idmod': int(x['idmod']), 'title':x['title'], 'url':host_url+x['files_android'][0], 'size': 0}
                            for x in js['packs'] if 'files_android' in x and x['files_android']
                        }
            self.pages = len(self.mods)/self.mods_on_page
            invoke_in_thread(self.set_mods_info, self.mods.values())
            self.resort_mods()
            self.drop_mods()
        except Exception as e:
            print(u'Неудалось десериализировать моды ' + str(e))

    def get_page(self, page=0):
        return self.sorted_mods[page*self.mods_on_page:(page+1)*self.mods_on_page]
    
    def resort_mods(self, func=None):
        if func:
            self.sorting_func = func
        self.sorted_mods = list(self.mods.values())
        self.sorted_mods.sort(key=self.sorting_func)
        for x in self.local_mods:
            self.sorted_mods.remove(x)
            self.sorted_mods.insert(0, x)
    
    def delete_mod(self, mod_id):
        self.local_mods[mod_id].delete()
        del self.local_mods[mod_id]

    # Загрузка
    def download_mod_worker(self, mod_id):
        self.processing = True
        mod = self.mods[mod_id]
        try:
            self.download = Downloading(**mod)
            key, val = self.download.process()
            self.local_mods[key] = val
        except Exception as exp:
            print(exp)
            self.progress = u'Ошибка' + str(exp)
        finally:
            self.processing = False

    def set_mods_info(self, mds):
        for i, m in enumerate(mds):
            if (i+1) % 100 == 0:
                restart_interaction()
            if m['size'] == 0:
                fp = urllib2.urlopen(m['url'])
                m['size'] = float(fp.headers['content-length'])/Mb
                m['last_modified'] = time.mktime(time.strptime(fp.headers['Last-Modified'], "%a, %d %b %Y %H:%M:%S %Z"))
        self.drop_mods()
        
    def get_size(self, fp=None, url=None):
        try:
            if fp is None:
                fp = urllib2.urlopen(url)
            print(fp.headers)
            return float(fp.headers['content-length'])/Mb
        except Exception as exp:
            print(exp)
            return -1

    def invoke_download(self, mod_id):
        #self.download_mod_worker(mod_id)
        invoke_in_thread(self.download_mod_worker, mod_id)

mlobj = ModLoader()