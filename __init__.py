from mycroft import MycroftSkill, intent_file_handler


class MoonlightEmbedded(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('embedded.moonlight.intent')
    def handle_embedded_moonlight(self, message):
        self.speak_dialog('embedded.moonlight')


def create_skill():
    return MoonlightEmbedded()

