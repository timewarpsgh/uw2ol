import pygame
import pygame_gui


def handle_gui_event(self, event):
    # pass event to gui manager
    self.ui_manager.process_events(event)

    # if event type is gui event
    if event.type == pygame.USEREVENT:

        # entry box entered
        if (event.user_type == pygame_gui.UI_TEXT_ENTRY_FINISHED and
                        event.ui_object_id == '#main_text_entry'):
            entry_box_entered(self, event)

        # button pressed
        elif event.user_type == pygame_gui.UI_BUTTON_PRESSED:
            button_pressed(self, event)

        # selection list
        elif event.user_type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            selection_list_picked(self, event)

def entry_box_entered(self, event):
    if event.text:
        # send
        self.change_and_send('speak', [event.text])

        # clear
        self.text_entry.set_text('')
        self.text_entry.unfocus()
        self.text_entry_active = False
        print("entered:", event.text)

def button_pressed(self, event):
    # normal buttons
    if event.ui_element in self.buttons:
        self.buttons[event.ui_element]()

    # buttons in windows
    elif event.ui_element in self.buttons_in_windows:

        # get dict value
        window = self.menu_stack[-1]
        dict = window.dict
        dict_value = dict['OK']

        # if value is list
        if isinstance(dict_value, list):
            protocol_name = dict_value[0]

            params_list = []
            for input_box in self.active_input_boxes:
                text = input_box.get_text()

                if text.isdigit():
                    text = int(text)

                params_list.append(text)

            self.change_and_send(protocol_name, params_list)

        # value is function
        else:
            self.buttons_in_windows[event.ui_element]()

def selection_list_picked(self, event):
    if event.ui_element == self.selection_list_stack[-1]:
        window = self.menu_stack[-1]
        dict = window.dict
        dict_value = dict[event.text]

        if isinstance(dict_value, list):
            function = dict[event.text][0]
            function(dict_value[1])
        else:
            dict[event.text]()