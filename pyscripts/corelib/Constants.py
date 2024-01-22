class Constants:

    RESET = '\033[0m'
    BOLD = '1;'
    BOLD = '1;'
    FAINT = '2;'  # Not widely supported
    ITALIC = '3;'
    UNDERLINE = '4;'
    SLOW_BLINK = '5;'
    FAST_BLINK = '6;'  # Not widely supported

    TEXT_BLACK = '0'
    TEXT_RED = '31'
    TEXT_GREEN = '32'
    TEXT_BROWN = '33'
    TEXT_BLUE = '34'
    TEXT_PURPLE = '35'
    TEXT_CYAN = '36'
    TEXT_LIGHT_GRAY = '37'
    TEXT_DARK_GRAY = BOLD + TEXT_BLACK
    TEXT_LIGHT_BLUE = BOLD + TEXT_BLUE
    TEXT_LIGHT_GREEN = BOLD + TEXT_GREEN
    TEXT_LIGHT_CYAN = BOLD + TEXT_CYAN
    TEXT_LIGHT_RED = BOLD + TEXT_RED
    TEXT_LIGHT_PURPLE = BOLD + TEXT_PURPLE
    TEXT_YELLOW = BOLD + TEXT_BROWN
    TEXT_WHITE = BOLD + TEXT_LIGHT_GRAY
    TAB = '\t'

    PACKAGEINFO_STARTSTOP = 'sbautomation'
    PACKAGEINFO_DEPLOYMENT = 'deployment'
   
    def colorize(message, color):
        return '\033[' + color + 'm' + message + Constants.RESET
