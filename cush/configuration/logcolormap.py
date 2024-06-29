'''
This dict is imported by the logging configuration file
and used as an argument to configure the colorlog.ColorFormatter object
for the colored logging output.

If there is a way to declare it in the config file itself, I haven't figured it out yet,
so it lives here and is imported into the YAML config via an external object specifier
'''

import kaleidoscope

cush_log_color_map = {
    'DEBUG'     : [kaleidoscope.Color('normal lightcyan on black'),
                   kaleidoscope.Color('normal cyan on black'),
                   kaleidoscope.Color('bright lightcyan on black')],

    'INFO'      : [kaleidoscope.Color('normal lightgreen on black'),
                   kaleidoscope.Color('normal green on black'),
                   kaleidoscope.Color('bright lightgreen on black')],

    'WARNING'   : [kaleidoscope.Color('bright black on lightyellow'),
                   kaleidoscope.Color('normal yellow on black'),
                   kaleidoscope.Color('bright lightyellow on black')],

    'ERROR'     : [kaleidoscope.Color('bright lightwhite on red'),
                   kaleidoscope.Color('normal red on black'),
                   kaleidoscope.Color('bright lightred on black')],

    'CRITICAL'  : [kaleidoscope.Color('bright lightyellow on magenta'),
                   kaleidoscope.Color('bright lightyellow on magenta'),
                   kaleidoscope.Color('bright lightyellow on magenta')]
}


thewired_log_color_map = {
    'DEBUG'     : [kaleidoscope.Color('normal lightcyan on black'),
                   kaleidoscope.Color('normal cyan on black'),
                   kaleidoscope.Color('bright lightcyan on black')],

    'INFO'      : [kaleidoscope.Color('normal lightgreen on black'),
                   kaleidoscope.Color('normal green on black'),
                   kaleidoscope.Color('bright lightgreen on black')],

    'WARNING'   : [kaleidoscope.Color('bright black on lightyellow'),
                   kaleidoscope.Color('normal yellow on black'),
                   kaleidoscope.Color('bright lightyellow on black')],

    'ERROR'     : [kaleidoscope.Color('bright lightwhite on red'),
                   kaleidoscope.Color('normal red on black'),
                   kaleidoscope.Color('bright lightred on black')],

    'CRITICAL'  : [kaleidoscope.Color('bright lightyellow on red'),
                   kaleidoscope.Color('bright lightyellow on red'),
                   kaleidoscope.Color('bright lightyellow on red')]
}

kaleidoscope_log_color_map = {
    'DEBUG'     : [kaleidoscope.Color('normal lightcyan on blue'),
                   kaleidoscope.Color('normal cyan on blue'),
                   kaleidoscope.Color('bright lightcyan on blue')],

    'INFO'      : [kaleidoscope.Color('normal lightgreen on blue'),
                   kaleidoscope.Color('normal green on blue'),
                   kaleidoscope.Color('bright lightgreen on blue')],

    'WARNING'   : [kaleidoscope.Color('bright blue on lightyellow'),
                   kaleidoscope.Color('normal yellow on blue'),
                   kaleidoscope.Color('bright lightyellow on blue')],

    'ERROR'     : [kaleidoscope.Color('bright lightwhite on red'),
                   kaleidoscope.Color('normal red on blue'),
                   kaleidoscope.Color('bright lightred on blue')],

    'CRITICAL'  : [kaleidoscope.Color('bright lightyellow on magenta'),
                   kaleidoscope.Color('bright lightyellow on magenta'),
                   kaleidoscope.Color('bright lightyellow on magenta')]
}
