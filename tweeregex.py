# regexes
LINK_REGEX = r"\[\[([^\|\]]*?)(?:\|(.*?))?\](\[.*?\])?\]"
MACRO_REGEX = r"<<([^>\s]+)(?:\s*)((?:[^>]|>(?!>))*)>>"
IMAGE_REGEX = r"\[([<]?)(>?)img\[(?:([^\|\]]+)\|)?([^\[\]\|]+)\](?:\[([^\]]*)\]?)?(\])"
HTML_BLOCK_REGEX = r"<html>((?:.|\n)*?)</html>"
HTML_REGEX = r"<(?:\/?\w+|\w+(?:(?:\s+\w+(?:\s*=\s*(?:\".*?\"|'.*?'|[^'\">\s]+))?)+\s*|\s*)\/?)>"
INLINE_STYLE_REGEX = "@@"
MONO_REGEX = r"^\{\{\{\n(?:(?:^[^\n]*\n)+?)(?:^\}\}\}$\n?)|\{\{\{((?:.|\n)*?)\}\}\}"
COMMENT_REGEX = r"/%((?:.|\n)*?)%/"

COMBINED_REGEX = '(' + ')|('.join([ LINK_REGEX, MACRO_REGEX, IMAGE_REGEX, HTML_BLOCK_REGEX, HTML_REGEX, INLINE_STYLE_REGEX,\
                    MONO_REGEX, COMMENT_REGEX, r"''|\/\/|__|\^\^|~~|==" ]) + ')'

# macro param regex - string or number or boolean or variable
# (Mustn't match all-digit names)
MACRO_PARAMS_VAR_REGEX = r'(\$[\w_\.]*[a-zA-Z_\.]+[\w_\.]*)'

# This isn't included because it's too general - but it's used by the broken link lexer
# (Not including whitespace between name and () because of false positives)
MACRO_PARAMS_FUNC_REGEX = r'([\w\d_\.]+\((.*?)\))'

MACRO_PARAMS_REGEX = r'(?:("(?:[^\\"]|\\.)*"|\'(?:[^\\\']|\\.)*\'|(?:\[\[(?:[^\]]*)\]\]))' \
    +r'|\b(\-?\d+\.?(?:[eE][+\-]?\d+)?|NaN)\b' \
    +r'|(true|false|null|undefined)' \
    +r'|'+MACRO_PARAMS_VAR_REGEX \
    +r')'
