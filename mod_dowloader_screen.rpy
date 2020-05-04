init python:
    from mod_downloader_script import mlobj
    mods['mod_downloader'] = "Загрузка модов"

label mod_downloader:
    #$ mlobj = ModLoader()
    call screen mod_loader

screen mod_loader(page=0):

    # Штука для обновления статуса скачивания
    #$ status = mlobj.progress
    #if mlobj.progress: # Хз почему по другому не работает нормально
    #    timer 0.5 repeat True action SetVariable(status, mlobj.progress)
        #TODO: попробовать вместо этого вызывать renpy.exports.restart_interaction
    

    text mlobj.progress:
        xalign 1.0 yalign 0.0
        

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
                        if mod['idmod'] in mlobj.local_mods:
                            text_color "#A00"
                            action Function(mlobj.delete_mod, mod['idmod'])
                        else:
                            text_color "#aaa"
                            action Function(mlobj.invoke_download, mod['idmod'])

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