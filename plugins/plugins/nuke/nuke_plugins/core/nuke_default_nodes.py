import os, nuke

class kitsu_write_node:

    def get_write_path(self, write_node):
        try:
            kitsu_env = [os.environ['KITSU_PROJECT'], os.environ['KITSU_SEQUENCE'], os.environ['KITSU_SHOT']]
            if any(x == '' for x in kitsu_env ):
                return False
            
            try:
                passname = write_node['pass_name'].value()
                is_edit = write_node['edit_path_mode'].value()
            except:
                write_node.addKnob(nuke.String_Knob('pass_name', 'pass name', 'mastercomp'))
                write_node.addKnob(nuke.Boolean_Knob('edit_path_mode', 'path is editable', False))
                write_node['User'].setLabel('SETTINGS')
                
            project = os.environ['KITSU_PROJECT_ROOT']
            sequence = os.environ['KITSU_SEQUENCE']
            shot = os.environ['KITSU_SHOT']
            file = nuke.Root().name()
            passname = write_node['pass_name'].value()
            version = nuke.Root().name().rsplit("_", 1)[-1][:-3]
            filename = os.path.basename(file)[:-3]
            if passname == '' or passname == None:
                passname = 'mastercomp'
            render_path = os.path.join(project,'shot', sequence, shot, 'media', 'comp_renders', passname, version, shot+'_'+passname+'_'+version+'.####.exr')

            write_node['file'].setEnabled(write_node['edit_path_mode'].value())
            render_path = render_path.replace('\\', '/')
            
            return render_path
            
        except Exception as eee:
            write_node['file'].setEnabled(True)
            return False
            
    def update_write_node(self, write_node, knob):

        if knob.name() == 'edit_path_mode':
            write_node['file'].setEnabled(write_node['edit_path_mode'].value())

        if any(x == knob.name() for x in ['pass_name', 'file_type']):
            old_file = self.get_write_path(write_node)
            if old_file and write_node['edit_path_mode'].value() == False:
                if any(x == write_node['file_type'].value() for x in ['mov', 'mxf']):
                    file_path = old_file[:-8]+write_node['file_type'].value()
                else:
                    file_path = old_file[:-4]+'.'+write_node['file_type'].value()
                
                write_node['file'].setValue(file_path)
                
    def create_write_node(self):            
        node = nuke.thisNode()    
        path = self.get_write_path(nuke.thisNode())

        if path:
            node['file'].setValue(path)
            node['knobChanged'].setValue("from core import nuke_default_nodes\nnuke_default_nodes.kitsu_write_node().update_write_node(nuke.thisNode(), nuke.thisKnob())")
        else:
            nuke.tprint('No Kitsu, Switching to normal Write')

    def refresh_write_nodes(self):
        for node in nuke.allNodes('Write'):
            try:
                version = os.path.basename(nuke.Root().name())[:-3].split('_')[-1]
                old_file_path = node['file'].value()
                old_file_split = os.path.join(os.path.dirname(os.path.dirname(old_file_path)),version,os.path.basename(old_file_path).split('_v')[0]+'_'+version+os.path.basename(old_file_path).split('_v')[1][4:])
                node['file'].setValue(str(old_file_split).replace('\\','/'))
            except Exception as eee:
                pass

ksw = kitsu_write_node()
nuke.addOnScriptSave(ksw.refresh_write_nodes)
nuke.addOnCreate(ksw.create_write_node, nodeClass="Write")
#nuke.menu( 'Nodes' ).addCommand( 'Image/Write', lambda: nuke.createNode( 'Write' ), 'w')

print('[ SUCCES !!! ] : nuke-default-nodes')