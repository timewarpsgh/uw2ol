Introduction to Project uw2ol(Uncharted Waters 2 Online)

    Goal
       An MMO that's essentially Uncharted Waters 2

    Methods

       Code
           Language
                Python only(for both client and server)
           Frameworks
                twisted(event driven network engine)
                pygame(game engine)
                pygame_gui(GUI engine)

       Assets
            All taken directly from the original game
            Could be replaced later if necessary

    Current Files

        Source

            Client Only
                assets(folder)
                    all images

                client
                    starts a client

                client_packet_received
                    handles packets from server
                draw
                game
                    game loop
                gui
                handle_gui_event
                    such as menu click, input box,
                handle_pygame_event
                    handles key presses, mouse clicks
                map_maker
                    makes port map and world map



            Server Only
                data(folder)
                    holds players' game role data(couldn't store in MySQL)
                    players' accounts in MySQL
                data_backup(folder)
                    backup for players' data

                DBmanager
                    interacts with MySQL(register, login, make character)
                server_1
                    starts the server
                server_packet_received
                    handles packets from clients

            For Both
                hashes(folder)
                    all data files, mostly dictionaries

                constants
                    configurations

                discovery
                    class(e.g: Panda, The Great Wall)

                event
                    class(a dialogue session occurs when an event is triggered)

                port
                    class

                protocol
                    class(packets transmitted between C and S)

                role
                    class(the player's role in game. has name, can move...)
                    All methods of the role class can be directly called by the client.
                    When a role(client) calls a method, the client runs the method locally,
                    and then sends the method to the server. When the server receives the method(protocol),
                    it runs the method on the server side copy of the role, and broadcasts the method to all
                    other roles that are currently in the role's map(either, port, sea, or battle).

                test
                    for testing anything

                translator
                    translates English to another language(not using yet)
                    pygame_gui, the GUI engine used, doesn't support any language other than English.
                    A issue has been raised on it's git page, but... who knows.

        Release
            dist(folder)
                an exe plus a folder for assets

        Documents
            ReadME
                overview of this project
            design
                how to dos
                what to dos(Requests here!)
            main_story
                the storyline
    Run it

        Coming soon...