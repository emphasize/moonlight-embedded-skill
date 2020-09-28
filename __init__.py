import subprocess, sys, re
from mycroft import MycroftSkill, intent_file_handler
from lingua_franca.format import join_list
from mycroft.util.parse import match_one
from mycroft.util.log import LOG
from mycroft.audio import wait_while_speaking

class MoonlightEmbedded(MycroftSkill):
    def __init__(self):
        super().__init__()

    def initialize(self):
        """ Perform any final setup needed for the skill here.
        This function is invoked after the skill is fully constructed and
        registered with the system. Intents will be registered and Skill
        settings will be available."""
        my_setting = self.settings.get('my_setting')
        # initial setup of config defaults:
        # prime default_config
        if 'default_config' not in self.settings:
            self.settings['default_config'] = "startup_config"
        if 'default_host' not in self.settings:
            self.settings['default_host'] = ""
        if 'host_list' not in self.settings:
            self.settings['host_list'] = []
        if 'config_list' not in self.settings:
            self.settings['config_list'] = []
        self.cmd = 'moonlight'

    def validate_answer(string):
        val_list = self.translate_list(self.dialog_answers)
        for word in val_list:
            if word in string:
                return word

    def test_connection(host):
        test = subprocess.Popen(['dig', host], stdout=subprocess.PIPE)
        sys.stdout.flush()
        for line in iter(test.stdout.readline, ''):
            if ';; ANSWER SECTION:' in line.rstrip():
                return True

        return False

    def check_config_for_content(config, list):
        for i in list:
            with open(config,"r") as f:
                new_f = f.readlines()
                f.seek(0)
                for line in new_f:
                    if i in line:
                        return True

        return False

    @intent_file_handler('list.apps.intent')
    def handle_app_list(self, host=None, spoken=True):
        MAX_LIST_ELEMENTS = 10

        if not host:
            if len(self.settings.get('default_host')) = 0:
                self.speak_dialog('pair.no.client')
                return

            else:
                host = self.settings.get('default_host')

        app_list=[]
        list_stdout = subprocess.Popen(['moonlight', 'list', host], stdout=subprocess.PIPE)
        sys.stdout.flush()
        for line in iter(list_stdout.stdout.readline, ''):
            match = research("(?<=^\d\.\ )[A-Za-z0-9_\.' -]+", line.rstrip())
            # knocks out duplicates
            if match not in app_list:
                app_list.append(match)
        if spoken:
            if len(app_list) < MAX_LIST_ELEMENTS-1:
                self.speak_dialog('list.apps', data={'list': self.join_list(app_list, self.translate("and", self.lang))})
            else:
                self.speak_dialog('list.apps.too.long')
                wait_while_speaking()
                #for word in sorted(list, key=str.lower):
                app_list_slice = []
                letter_list= []
                tmp_list = []
                tmp_list2 = []
                i=0
                for letter, words in groupby(sorted(app_list, key=str.lower), key=itemgetter(0)):
                    for word in words:
                        tmp_list.append(word)
                        tmp_list2.append(letter)
                        if len(tmp_list)>MAX_LIST_ELEMENTS-1:
                            app_list_slice.append(list(tmp_list))
                            letter_list.append(list((i, tmp_list2)))
                            first_letter=letter_list[i][1][0]
                            last_letter=letter_list[i][1][MAX_LIST_ELEMENTS-1]
                            self.speak_dialog('list.app.parts', data={'number':i+1, 'first_letter':first_letter, 'last_letter': last_letter})
                            wait_while_speaking()
                            tmp_list=[]
                            tmp_list2=[]
                            i+=1
                letter_list.append(list((i, tmp_list2)))
                app_list_slice.append(list(tmp_list))
                first_letter=letter_list[i][1][0]
                last_letter=letter_list[i][1][len(letter_list[i][1])-1]
                self.speak_dialog('list.app.parts', data={'number':i, 'first_letter':first_letter, 'last_letter': last_letter})
                wait_while_speaking()
                response = self.get_response('list.apps.which.bracket')
                self.speak_dialog('list.apps', data={'list': self.join_list(app_list_slice[response-1], self.translate("and", self.lang))})

                return

        return list


    @intent_file_handler('list.hosts.intent')
    def handle_list_hosts(self, message):
        host_list = self.settings.get('host_list')
        if len(host_list)>0:
            self.speak_dialog('list.hosts', data={'host_list': self.join_list(host_list, self.translate("and", self.lang))})
        else:
            self.speak_dialog('pair.no.client')

    @intent_file_handler('host.set.default.intent')
    def handle_set_default_host(self, message):
        host_list = self.settings.get('host_list')
        host = self.message.data['host']
        while not test_connection(host):
            host = self.get_response('host.not.found')
        if host not in host_list:
            self.speak_dialog('host.not.paired', data={'host': host})
            handle_pair_request(message)
        else:
            self.settings['default_host']= host


    @intent_file_handler('check.connection.intent')
    def handle_check_connection(self, message):
        host = self.settings.get('default_host')
        if not test_connection(host):
            self.speak_dialog('test.connection.failed', data={'host': host})
        else:
            if not self.handle_app_list(host,spoken=False):
                self.speak_dialog('test.connection.failed', data={'host': host})
            else:
                self.speak_dialog('test.connection.success', data={'host': host})


    @intent_file_handler('pair.intent')
    def handle_pair_request(self, message):
        host = message.data["host"]
        while not test_connection(host):
            i += 1
            if i>3:
                self.speak_dialog('breaking.up')
                return False
            host = self.get_response('host.not.found')
        pair = subprocess.Popen(['moonlight', 'pair', host], stdout=subprocess.PIPE)
        sys.stdout.flush()
        for line in iter(pair.stdout.readline, ''):
            #searching for a 3-6 digit number
            match = research('(?<=\:\ )\d{3,6}', line.rstrip())
            already_paired = research('(?<=\:\ )(Already paired)', line.rstrip())
            if already_paired:
                self.speak_dialog('pair.already.done', data={'host': host})
                return
        self.speak_dialog('pair', data={'number': match})
        self.settings['host_list'].append(host)
        self.settings['default_host'] = host
        return True

    @intent_file_handler('config.wizard.intent')
    def handle_setup_wizard(self, message, overwrite=True):
    #take the staged approach (Prio I then ask to go further ..)
    """
                 Streaming options                                                                                                                  Priority
                    -app <app>              Name of app to stream                                                                                 (I | II | III)
    ---------       -------------------------------------------------------------------------------------------------------------------------
                    -720                    Use 1280x720 resolution [default]                                                                       I
                    -1080                   Use 1920x1080 resolution
      video         -4k                     Use 3840x2160 resolution
                    -width <width>          Horizontal resolution (default 1280)                                                                    I
                    -height <height>        Vertical resolution (default 720)
                    -fps <fps>              Specify the fps to use (default -1)                                                                         II
                    -codec <codec>          Select used codec: auto/h264/h265 (default auto)                                                            II
    ---------
                    -surround               Stream 5.1 surround sound (requires GFE 2.7)                                                            I
      audio         -localaudio             Play audio locally on the host computer                                                                 I
    ---------
                    -bitrate <bitrate>      Specify the bitrate in Kbps                                                                                 II
     network        -packetsize <size>      Specify the maximum packetsize in bytes                                                                     II
    ---------
                    -nosops                 Don't allow GFE to modify game settings                                                                     II
 optimization       TODO: Not clear what -remote does -> excluded so far
                    #-remote                 Enable remote optimizations                                                                                II
                    --------------------------------------------------------------------------------------------------------------------------
                    -keydir <directory>     Load encryption keys from directory
                    -mapping <file>         Use <file> as gamepad mappings configuration file
                    -platform <system>      Specify system used for audio, video and input: pi/imx/aml/rk/x11/x11_vdpau/sdl/fake (default auto)      =terminal
                    -unsupported            Try streaming if GFE version or options are unsupported
                    -quitappafter           Send quit app request to remote after quitting session
                    -viewonly               Disable all input processing (view-only mode)
    """
    wizard_seq = [('resolution', '0'), ('surround', '1'), ('localaudio', '1'), ('nosops', '1'), ('ask_further', '1'), ('fps', '0'), ('bitrate', '0'), ('packetsize', '0'), ('codec', '0')]
    self.settings['new_config']=[]
    default_conf=self.settings.get('default_config')
    res_dict = {'720':('1024','720'),'1080':('1920','1080'),'4k':('3840','2160')}

    if default_conf = "startup_config":
        self.speak_dialog('config.initial')
        if overwrite:
            #Noch unsicher
            overwrite = False

    # Look if specific config changes are intended and change the sequence if true
    specific_config = self.message.data['specific_config']
    LF_specific_config = self.translate_list('config.specific')
    if overwrite and specific_config:
        switcher = {
            LF_specific_config[0]: "[('resolution', '0'), ('fps', '0'),('codec', '0')]"
            LF_specific_config[1]: "[('surround', '1'), ('localaudio', '1')]"
            LF_specific_config[2]: "[('bitrate', '0'), ('packetsize', '0')]"
            LF_specific_config[3]: "[('nosops', '1')]"
        }
        wizard_seq = switcher.get(specific_config)

    self.log.info(wizard_seq)

    # the core sequence iteration
    for config_name, type in wizard_seq :
        self.dialog = 'config.'+config_name
        self.dialog_answers = dialog+'.answer'
        self.dialog_followup = dialog+'.followup'
        if type = 0:
            #The configs that got defaults and/or are considered 'advanced' got a
            #introductory line to further explain the setting and its options
            response = self.ask_yesno(dialog)
            while  response != 'yes' && response != 'no':
                response = self.ask_yesno(dialog)
            if  response = 'yes':
                response=self.get_response(dialog_followup, validator=validate_answer)
                if dialog = 'config.resolution.followup' and response = self.voc_match(response, 'custom'):
                    custom_res_X = self.get_response('config.resolution_customX')
                    custom_res_Y = self.get_response('config.resolution_customY')
                    if overwrite:
                        if check_config_for_content(default_conf, ['width', 'height']):
                            delete = '/^(width|height)/d'
                            subprocess.call(['sed', '-ri', delete, default_conf])
                        add='1iwidth = '+custom_res_X+'\\nheight = '+custom_res_Y
                        subprocess.call(['sed', '-i', add, default_conf])
                    else:
                        self.settings['new_config'].append(('-width '+custom_res_X))
                        self.settings['new_config'].append(('-height '+custom_res_Y))
                else:
                    if config_name = 'resolution':
                        if overwrite:
                            if check_config_for_content(default_conf, ['width', 'height']):
                                delete = '/^(width|height)/d'
                                subprocess.call(['sed', '-ri', delete, default_conf])
                            for i in res_dict:
                                if i == response:
                                    width, height = res_dict[i]
                            add='1iwidth = '+width+'\nheight = '+height
                            subprocess.call(['sed', '-i', add, default_conf])
                        else:
                            self.settings['new_config'].append(('-'+response))
                    else:
                        if overwrite:
                            if check_config_for_content(default_conf, [config_name]):
                                delete='/^'+config_name+'/d'
                                subprocess.call(['sed', '-i', delete, default_conf])
                            add='$a'+config_name+' = '+response
                            subprocess.call(['sed', '-i', '-e', add, default_conf])
                        else:
                            self.settings['new_config'].append(('-'+config_name+' '+response))
            else:
                if overwrite:
                    if config_name = 'resolution':
                        if check_config_for_content(default_conf, ['width', 'height']):
                            delete = '/^(width|height)/d'
                            subprocess.call(['sed', '-ri', delete, default_conf])
                    else:
                        if check_config_for_content(default_conf, [config_name]):
                            delete='/^'+config_name+'/d'
                            subprocess.call(['sed', '-i', delete, default_conf])
        else:
            response = self.ask_yesno(dialog)
            while  response != 'yes' && response != 'no':
                response = self.ask_yesno(dialog)
            if config_name = 'ask.further' && response='no':

                break

            else if response = 'yes':
                if overwrite:
                    if check_config_for_content(default_conf, [config_name]):
                        delete = '/^'+config_name+'/d'
                        subprocess.call(['sed', '-ri', delete, default_conf])
                    add='$a'+config_name
                    subprocess.call(['sed', '-i', add, default_conf])

                self.settings['new_config'].append(('-'+config_name))
            else:
                if overwrite:
                    if check_config_for_content(default_conf, [config_name]):
                        delete='/^'+config_name+'/d'
                        subprocess.call(['sed', '-i', delete, default_conf])

    if not overwrite:
        name = self.get_response('config.name')
        self.settings['new_config'].append(('-save '+name))
        self.settings['config_list'].append(name)

    return name #of the config_file

    def cmd_contructor(app='', host=''):
    config = self.settings.get('default_config')
    option_str=''
    app_cmd=''

    # push to handle_setup_wizard to create a new config
    if config = 'startup_config':
        name = handle_setup_wizard(overwrite=False)
    # if a new_config is available, the command looks like
    # moonlight [action] [-app ..] (new_options) -save name [host]
    # with the named save_file written to disk and handled as default_config
    # this deals with the stringed part "(new_options) -save name"
    if len(self.settings.get('new_config',[])) > 0:
        option_str = " ".join((self.settings.get('new_config',[])))
        option_str = option_str + ' '
        self.log.info("options :" + option_str)
        self.settings['default_config'] = [name]
        self.log.info("new default_option: " + name)
        self.settings['new_config']=[]
        #self.log.info("List new_config: " + str(self.settings.get('new_config',[])))
    else:
        option_str += '-config ' + self.settings.get('default_config') + ' '
    if host = '':
        if len(self.settings.get('default_host')) = 0:
            host = self.get_response('specify.host')
            while not test_connection(host):
                host = self.get_response('host.not.found')
            #TODO break if multiple misconnects occur
            if host not in self.settings.get('host_list'):
                if not handle_pair_request(message.data['host']=host)
                    return False
            host_cmd = host.rjust(len(host)+1, ' ')
        else:
            host = self.settings.get('default_host')
            host_cmd = host.rjust(len(host)+1, ' ')
    else:
        #check host if host was passed to confirm existence
        while not test_connection(host):
            host = self.get_response('host.not.found')
        if host not in self.settings['host_list']:
            if not handle_pair_request(message.data['host']=host)
                return False
        host_cmd = host.rjust(len(host)+1,' ')
    if app != '':
        # maybe in start_stream
        app_list = self.handle_app_list(host, spoken=False)
        if app not in app_list:
            i=0
            for i<3:
                if i>0:
                    app = self.get_response('app.alternative')
                best_match = self.match_one(app, app_list)[0]
                response = self.ask_yesno('app.misspelled', data={'best_match': best_match})
                i+=1
                if response = 'yes':
                    break

            else:
                self.speak_dialog('breaking.up')
                #maybe hint at the list_apps.intent
                return False

        app_cmd = ' -app ' + app.rjust(len(app)+1,' ')

    cmd_str = self.cmd + ' stream ' + app_cmd + option_str + host_cmd
    self.log.info("cmd : "+cmd_str)
    return cmd_str


    @intent_file_handler('config.new.intent')
    def handle_new_config_file(self, message):
        name = self.handle_setup_wizard(message, overwrite=False)

        return


    @intent_file_handler('stream.start.intent')
    def handle_start_stream(self, message):  #, host=default_host(), config=default_config()
        self.log.info("App: " + message.data["app"])
        host = message.data["host"] || ''
        app = message.data["app"] || ''
        cmd_str = cmd_contructor(app, host)
        if cmd_str:
            subprocess.Popen(cmd_str, shell=True)
            self.speak_dialog('moonlight.start')
        return True

    @intent_file_handler('quit.stream.intent')
    def handle_quit_stream(self, message):
        subprocess.Popen("kill $(ps | grep 'moonlight' | awk '{ print $1 }')", shell=True)
        self.speak_dialog('moonlight.quit')
        return True

def create_skill():
    return MoonlightEmbedded()
