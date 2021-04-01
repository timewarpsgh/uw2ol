str = "你"*20


def to_multi_lines(msg):
    """turn a single line of chinese to multiple lines"""
    text_count = len(msg)
    lines = (text_count // 12) + 1

    new_msg = ''

    for line in range(lines):
        new_msg += f"{msg[line*12:(line+1)*12]}"\

    print(new_msg)

to_multi_lines(str)