import nuke, gazu, os

class nuke_boot_setup:
    def __init__(self):

        gazu.set_host(os.getenv('KITSU_HOST')+'/api')
        token = {'access_token': os.getenv('KITSU_ACCESS_TOKEN')}
        gazu.client.set_tokens(token)
        
        self.project = gazu.project.get_project_by_name(os.getenv('KITSU_PROJECT'))
        self.task = gazu.task.get_task(os.getenv('KITSU_CONTEXT_ID'))
        self.shot = self.task['entity']

        self.resolution = [int(x) for x in self.shot['data']['resolution'].split('x')]
        self.fps = self.shot['data']['fps']
        self.framerange = [self.shot['data']['frame_in'], self.shot['data']['frame_out']]
        
    def set_project_framerange(self):
        nuke.Root()['first_frame'].setValue(int(self.framerange[0]))
        nuke.Root()['last_frame'].setValue(int(self.framerange[1]))
        return [int(self.framerange[0]),int(self.framerange[1])]

    def set_project_resolution(self):
        nuke_format = str(self.resolution[0])+ ' ' + str(self.resolution[1]) +'  KITSU_FORMAT'
        nuke.addFormat(nuke_format)
        nuke.Root()['format'].setValue('KITSU_FORMAT')
        return nuke_format

    def set_project_frame_rate(self):
        nuke.Root()['fps'].setValue(float(self.fps))
        return self.fps

    def check_current_script(self):
        current_framerange = [nuke.Root()['first_frame'].value(), nuke.Root()['last_frame'].value()]
        current_rez = [nuke.Root().format().width(), nuke.Root().format().height()]
        current_fps = nuke.Root()['fps'].value()

        if current_framerange != self.framerange:
            mm = nuke.ask('We have detected a FRAMERANGE mismatch.\n\nCurrent Range : ' + str(current_framerange)+ '\nKitsu Range : '+ str(self.framerange)+'\n\nDo you want kitsu to set the framerange ?')
            if mm:
                self.set_project_framerange()
                
        if current_rez != self.resolution:
            mm = nuke.ask('We have detected a RESOLUTION mismatch.\n\nCurrent Resolution : ' + str(current_rez)+ '\nKitsu Resolution : '+ str(self.resolution)+'\n\nDo you want kitsu to set the resolution ?')
            if mm:
                self.set_project_resolution()
        if float(current_fps) != float(self.fps):
            mm = nuke.ask('We have detected a FPS mismatch.\n\nCurrent FPS : ' + str(current_fps)+ '\nKitsu FPS : '+ str(self.fps)+'\n\nDo you want kitsu to set the framerate ?')
            if mm:
                self.set_project_frame_rate()

        return 
        
def check_nuke_script():
    nuke_boot_setup().check_current_script()

print('[ SUCCES !!! ] : nuke-boot-checkups')
nuke.addOnScriptLoad(check_nuke_script)
