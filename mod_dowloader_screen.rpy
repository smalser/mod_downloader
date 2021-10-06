init python:
    config.developer = True
    config.console = True
    
init 10050000 python:
    config.debug = True
    config.console = True

init python:
    from md.mds import mlobj
    mods['mod_downloader'] = "Загрузка модов"
    mods['mod_downloader1'] = "Konsol"

label mod_downloader1:
    python:
        _console.enter()
    pause()


label mod_downloader:
    # $ mlobj = ModLoader()
    call screen mod_loader

screen mod_loader(page=0):

    $ mods = mlobj.get_page(page)
    window background get_image("gui/settings/preferences_bg.jpg") xalign 0.5 yalign 0.5:
        vbox:
            xalign 0.5
            xfill True
            text str(mlobj.progress) style "settings_link" xalign 0.5 color "#ffffff"
            #hbox:
            #    textbutton "Загруженные"
            #    textbutton "Все"
            #    
            hbox:
                xcenter 0.5
                xfill True
                for txt, to in (('По имени', 'name'), ('По размеру', 'size'), ('По дате', 'date')):
                    textbutton txt:
                        style "log_button" text_style "settings_link"
                        if mlobj.sorting == to:
                            text_color "#FFF"
                        else:
                            action Function(mlobj.sort, to)
        
        side "c r":
            #area (0.1, 0.24, 0.6, 0.70)
            area (0.275, 0.225, 0.48, 0.70)
            
            viewport id "mods":
                draggable True
                mousewheel True
                scrollbars None
                yinitial 0.0

                #has grid 2 len(mods)
                has vbox
                
                for mod in mods:
                    hbox:
                        text '|%.2f Mb|' % (mod['size']):
                            ycenter 0.5 xsize 300 xalign 1.0
                            color "#000"
                            
                        textbutton mod['title']:
                            xalign 0.0
                            ycenter 0.5
                            style "log_button" text_style "settings_text"
                            # Когда обрабатывается что-то
                            if mlobj.processing:
                                text_color "#AAA"
                                action NullAction()
                            elif mod['idmod'] in mlobj.local_mods:
                                text_color "#F00"
                                action Function(mlobj.delete_mod, mod['idmod'])
                            else:
                                #text_color "#aaa"
                                action Function(mlobj.invoke_download, mod['idmod'])

            #$ vbar_null = Frame(get_image("gui/settings/vbar_null.png"),0,0)
            vbar value YScrollValue("mods") bottom_bar "images/misc/none.png" top_bar "images/misc/none.png" thumb "images/gui/settings/vthumb.png" thumb_offset -12
    
        vbox:
            yalign 0.5 xalign 0.99
            
            imagebutton auto "images/gui/ipad/next_%s.png":
                if page < mlobj.pages:
                    action [Hide("mod_loader"), ShowMenu("mod_loader", page+1)]
            #null height 30
            #imagebutton auto "images/gui/dialogue_box/day/fast_forward_%s.png":
            #    if page < mlobj.pages:
            #        action [Hide("mod_loader"), ShowMenu("mod_loader", mlobj.pages)]
            
        vbox:
            yalign 0.5 xalign 0.01
            imagebutton auto "images/gui/ipad/prev_%s.png":
                if page > 0:
                    action [Hide("mod_loader"), ShowMenu("mod_loader", page-1)]
            #null height 30
            #imagebutton auto "images/gui/dialogue_box/day/fast_backward_%s.png":
            #    if page > 0:
            #        action [Hide("mod_loader"), ShowMenu("mod_loader", 0)]
    
    
    
    hbox:
        spacing 5
        xalign 1.0 ypos 0.9
        textbutton "Назад":
            ycenter 0.5
            if page > 0:
                action [Hide("mod_loader"), ShowMenu("mod_loader", page-1)]
            else:
                action NullAction()

        text "%d/%d" % (page+1, mlobj.pages+1) ycenter 0.5

        textbutton "Вперед":
            ycenter 0.5
            if page < mlobj.pages:
                action [Hide("mod_loader"), ShowMenu("mod_loader", page+1)]
            else:
                action NullAction()

    vbox:
        xalign 1.0 yalign 0.75
        textbutton "Exit" text_size 64 xcenter 0.5 action [Hide("mod_loader"), MainMenu(False)]
        textbutton "Reload" text_size 64 xcenter 0.5 action Function(renpy.utter_restart)