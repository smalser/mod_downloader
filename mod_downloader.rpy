init:
    $ mods['mod_downloader'] = "Загрузка модов"

label mod_downloader:
    $ mlobj = ModLoader()
    call screen mod_loader

init python:
    import os, io
    import json
    from io import BytesIO
    import urllib, urllib2, zipfile
    from renpy.exports import invoke_in_thread

    class ModLoader:    
        host_url = 'http://191.ru/es/'
        json_url = host_url + 'project2.json'
        files_path = os.environ["ANDROID_PUBLIC"]
        temp_folder = files_path + "downloads/"
        mods_on_page = 10
        
        def __init__(self):
            self.loaded = 0
            self.size = 0
            self.progress = "Загрузка не ведется"
            self.load_mods()
            
            try:
                os.mkdir(temp_folder)
            except: pass
            
        def load_mods(self):
            urllib.urlretrieve(self.json_url, 'project2.json')
            js = json.load(io.open('project2.json', 'r', encoding='utf-8'))
            self.mods = [{'title':x['title'], 'url':self.host_url+x['files_android'][0], 'size': 0}
            for x in js['packs'] if 'files_android' in x and x['files_android']]
            self.mods.sort(key=lambda x: x['title'])
            self.pages = len(self.mods)/self.mods_on_page
            return self.mods
        
        def get_page(self, page=0):
            mds = self.mods[page*self.mods_on_page:(page+1)*self.mods_on_page]
            for m in mds:
                if m['size'] == 0:
                    m['size'] = self.get_size(url=m['url'])
            return mds
        
        def download_mod_worker(self, url):
            self.progress = 'Загрузка...'
            #fname = self.temp_folder + url.split('/')[-1]
            fp = urllib2.urlopen(url)
            self.size = self.get_size(fp)
            bp = open('tmp.zip', 'wb')
            readed = fp.read(1024*1024)
            self.loaded = 1
            while readed:
                bp.write(readed)
                readed = fp.read(1024*1024)
                self.loaded += 1
                self.progress = "%dMb / %.2fMb" % (self.loaded, self.size)
            self.progress = "Распаковка..."
            bp.close()
            bp = 'tmp.zip'
            #bp.seek(0)
        
            zipfile.ZipFile(bp).extractall(self.files_path)
            
            self.progress = "Готово"
            
        def get_size(self, fp=None, url=None):
            try:
                if fp is None:
                    fp = urllib2.urlopen(url)
                return float(fp.headers['content-length'])/1024/1024
            except:
                return -1
            
        def invoke_download(self, url="http://191.ru/es/android/pioneersgame_Android.zip"):
            invoke_in_thread(self.download_mod_worker, url)


    mlobj = ModLoader()
    
screen mod_loader(page=0):

    # Штука для обновления статуса скачивания
    $ status = mlobj.progress
    if mlobj.progress: # Хз почему по другому не работает нормально
        timer 0.5 repeat True action SetVariable(status, mlobj.progress)
    
    text str(status):
        size 64 xalign 1.0 yalign 0.0

    $ mods = mlobj.get_page(page)
    window background Frame(get_image("gui/choice/day/choice_box.png"),50,50) left_padding 10 top_padding 10 right_padding 10 bottom_padding 10:
        area(0.0,0.0,0.75,0.95)
        side "c r":
            #viewport id "glory_ambience":
            #    draggable True
            #    mousewheel True
            #    scrollbars None

            #    has grid 1 len(mods)
            vbox:
                for mod in mods:
                    textbutton mod['title'] + '(%.2f Mb)' % mod['size']:
                        #style "log_button"
                        text_style "music_link"
                        text_color "#aaa"
                        action Function(mlobj.invoke_download, mod['url'])

            #$ vbar_null = Frame(get_image("gui/settings/vbar_null.png"),0,0)
            #vbar value YScrollValue("glory_ambience") bottom_bar vbar_null top_bar vbar_null thumb "images/gui/settings/vthumb.png" thumb_offset -10
    
    hbox:
        spacing 10
        xalign 1.0 ypos 0.9
        textbutton "Назад":
            ycenter 0.5
            if page > 0:
                action [Hide("mod_loader"), ShowMenu("mod_loader", page-1)]
            else:
                action NullAction()

        text "%d/%d" % (page, mlobj.pages) ycenter 0.5

        textbutton "Вперед":
            ycenter 0.5
            if page < mlobj.pages:
                action [Hide("mod_loader"), ShowMenu("mod_loader", page+1)]
            else:
                action NullAction()

    textbutton "Exit" text_size 64 xcenter 0.9 ypos 0.5 action [Hide("mod_loader"), MainMenu(False)]
    textbutton "Reload" text_size 64 xcenter 0.9 ypos 0.6 action Function(renpy.utter_restart)

    