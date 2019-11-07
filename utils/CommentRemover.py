### modified version of: http://www.cmycode.com/2016/02/program-for-remove-comments-c.html ###

COMMENT_START = '/'
ONELINE_COMMENT = 1
MULTILINE_COMMENT = 2

def removeComments(src):
    retsrc = ''
    escape = False
    comment_type = 0
    skip_new_line = False
    string_started = False
    comment_ending = False
    comment_started = False

    for c in src:

        if skip_new_line:
            skip_new_line = False
            if c == '\n':
                continue

        if comment_type == ONELINE_COMMENT:
            if c == '\\':
                escape = not escape
            elif c == '\n' and not escape:
                comment_type = 0
                comment_started = False
                retsrc += c
            else:
                escape = False
            continue

        if comment_type == MULTILINE_COMMENT:
            if comment_ending:
                if c == COMMENT_START:
                    comment_ending = False
                    comment_started = False
                    comment_type = 0
                    skip_new_line = True
                    continue
                comment_ending = False
            if c == '*':
                comment_ending = True
            continue

        if comment_started:
            if c == '*':
                comment_type = MULTILINE_COMMENT
                continue
            if c == COMMENT_START:
                comment_type = ONELINE_COMMENT
                continue
            retsrc += COMMENT_START
            comment_started = False

        if string_started:
            if c == '\\':
                escape = not escape
            elif c == '"' and not escape:
                string_started = False
            else:
                escape = False
            retsrc += c
            continue

        if c == '"':
            string_started = True

        if c == COMMENT_START:
            comment_started = True
            continue

        retsrc += c

    return retsrc
