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

        documents
            ReadME
                overview of this project
            requests
                to dos, including new requests and bug fix requests
            how_to_dos
                how to dos
                what to dos(Requests here!)
            main_story
                the story line
            python_lib_requirements

        assets
            all resources

        dist
            for distribution, an exe plus a folder for assets

        code
            client
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
                sprites
                    all spirets(anything you can see on screen) should be here.
                    some are not due to historical reasons.
                translator
                    translates english to other languages

            server
                data(folder)
                    holds players' game role data(couldn't store in MySQL, maybe later)
                    players' accounts are in MySQL
                data_backup(folder)
                    backup for stuff in data folder
                DBmanager
                    interacts with MySQL(register, login, make character)
                server_1
                    starts the server
                server_packet_received
                    handles packets from clients
                npc_manager
                    manages all npcs(fleet on the sea), port_npcs are managed locally
                player_manager
                    holds all online players

            common
                hashes(folder)
                    all data files, mostly dictionaries
                constants
                    configurations
                protocol
                    packets transmitted between C and S
                role
                    class(the player's role in game. has name, can move...)
                    All methods of the role class can be directly called by the client.
                    When a role(client) calls a method, the client runs the method locally,
                    and then sends the method to the server. When the server receives the method(protocol),
                    it runs the method on the server side copy of the role, and broadcasts the method to all
                    other roles that are currently in the role's map(either, port, sea, or battle) and nearby.
                test
                    for testing anything

    Run it
        You can run the server and multiple clients locally.

        1 get MySQL
            create a database named py_test
            set password to dab9901025
            create a table named accounts
                column name     data type    length  DEFAULT     PK?   NOT NULL?   AUTO INCR?
                id              int          11                  T     T           T
                name            char         12
                pw              char         12
                online          tinyint      1       0
                role            char         12

        2 get python and the missing libraries(consider using a mirror if it's slow)
            (if it misses a module named PIL, install Pillow instead)

        3 run server_1.py
        4 run client.pyw

        now you are in.

        shortcut to login:
            if you have an account like this:
                account 1
                password 1
            you can login by just pressing 1

            any number from 1-9 will work

    Join us
        contact any of the contributors to join us. test.

