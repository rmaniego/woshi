"""
    (c) 2022 Rodney Maniego Jr.
    Woshi
"""

import re
import time
import shlex
import threading
from io import StringIO
import lxml.etree as e3
from arkivist import Arkivist

class Woshi:
    def __init__(self, filepath=None, html=None):
        self.filepath = None
        if filepath is None:
            self.filepath = filepath
        self.html = _to_html_object(html)
        self.lock = threading.RLock()

    def __setitem__(self, xpath, ftml):
        with self.lock:
            if isinstance(xpath, str) and isinstance(ftml, str):
                xpath = xpath.strip()
                if not len(xpath):
                    return
            properties = _decode_ftml(ftml)
            if len(properties):
                rules = properties.get("rules", {})
                action = properties.get("action", "prop")
                if rules.get("xpath", 1):
                    xpath = _parse_selector(xpath)
                if xpath == "html" and action == "prop":
                    for child in self.html.getroot():
                        parent = child.getparent()
                        if parent.tag == "html":
                            attributes = properties.get("attributes", {})
                            for key, value in attributes.items():
                                parent.set(key, value)
                for match in self.html.findall(xpath):
                    if action == "prop":
                        attributes = properties.get("attributes", {})
                        for key, value in attributes.items():
                            match.set(key, value)
                    else:
                        tag = properties["tag"]
                        element = _to_html_object(_new_element(properties, match.tag), tag)
                        if element is None:
                            break
                        static = rules.get("static", 0)
                        if static:
                            if tag in ("link", "img", "script"):
                                attr = "href"
                                if tag in ("img", "script"):
                                    attr = "src"
                                for item in element.findall(tag):
                                    source = item.get(attr)
                                    item.set(attr, f"{{{{ url_for('static', filename='{source}') }}}}")
                        match.append(element)
                    fount = True
                
                    

    def append(self, xpath, ftml, is_html=False, to_xpath=True, static=False):
        with self.lock:
            if not is_html:
                self.__setitem__(xpath, ftml)
            else:
                if isinstance(xpath, str) and isinstance(ftml, str):
                    xpath = xpath.strip()
                    if not len(xpath):
                        return
                to_xpath = isinstance(to_xpath, bool) and bool(to_xpath)
                if to_xpath:
                    xpath = _parse_selector(xpath)
                for match in self.html.findall(xpath):
                    try:
                        tag = "".join(list(list(ftml.split(">"))[0].split(" "))[0][1:])
                    except:
                        assert False, "Woshi: Malformed HTML element:\n " + ftml
                    element = _to_html_object(ftml, tag)
                    if element is None:
                        break
                    static = isinstance(static, bool) and bool(static)
                    if static:
                        if tag in ("link", "img", "script"):
                            attr = "href"
                            if tag in ("img", "script"):
                                attr = "src"
                            for item in element.find_all(tag):
                                source = item.get(attr)
                                item.set(attr, f"{{{{ url_for('static', filename='{source}') }}}}")
                    match.append(element)

    def prop(self, xpath, ftml):
        self.__setitem__(xpath, ftml)

    def  __getitem__(self, xpath):
        with self.lock:
            xpath = _parse_selector(xpath)
            for match in self.html.findall(xpath):
                yield match
            else:
                return []

    def get(self, xpath, to_string=False):
        with self.lock:
            to_string = isinstance(to_string, bool) and bool(to_string)
            xpath = _parse_selector(xpath)
            for match in self.html.findall(xpath):
                html = match
                if to_string:
                    html = _to_string(html)
                yield html
            else:
                return []

    def build(self):
        with self.lock:
            return _to_string(self.html)

    def save(self, filepath=None):
        with self.lock:
            if filepath is None:
                filepath = self.filepath
            if isinstance(filepath, str):
                filepath = filepath.strip()
                if not len(filepath):
                    return
                if "/" in filepath:
                    if not _new_folders("/".join(filepath.split("/")[0:-1])):
                        return
                if filepath[-5:] != ".html":
                    filepath += ".html"
                _new_file(filepath, self.build())

def _parse_selector(selector):
    selector = selector.strip()
    if not(("/" in selector) or ("=" in selector)):
        if "#" in selector:
            temp = selector.split("#")
            if len(temp) == 2:
                parent_tag, attribute = temp
                parent_tag = parent_tag.strip()
                if len(parent_tag):
                    return f".//{parent_tag}[@id='{attribute}']"
        elif "." in selector:
            temp = selector.split(".")
            if len(temp) == 2:
                parent_tag, attribute = temp
                parent_tag = parent_tag.strip()
                if len(parent_tag):
                    return f".//{parent_tag}[@class='{attribute}']"
        else:
            return f".//{selector}"
    return selector

def _to_string(html, space=" "):
    if not isinstance(space, str):
        space = " "
    e3.indent(html, space=space)
    return e3.tostring(html, pretty_print=True, method="html").decode("utf-8")

def _to_html_object(html, tag=None):
    if not isinstance(html, str) or tag is None:
        html = "<html><head></head><body></body></html>"
        elements = e3.parse(StringIO(html), parser=e3.HTMLParser())
        elements.docinfo.public_id = None
        elements.docinfo.system_url = None
        return elements
    elements = e3.parse(StringIO(html), parser=e3.HTMLParser())
    if tag is None:
        return elements
    for element in elements.findall(".//"+tag):
        return element
    return elements

def _new_element(properties, parent=None):
    rules = properties.get("rules", {})
    
    formatted = []
    id = properties.get("id", "")
    if len(id):
        data.append(f"id=\"{id}\"")

    attributes = properties.get("attributes", {})
    for attribute, value in attributes.items():
        if len(value):
            cached = rules.get("cached", 1)
            if (attribute in ("href", "src")) and not cached:
                if "?" in value:
                    value = f"{value}&t=" + str(int(time.time()))
                else:
                    value = f"{value}?t=" + str(int(time.time()))
            formatted.append(f"{attribute}=\"{value}\"")
            continue
        formatted.append(attribute)
    
    escape = rules.get("escape", 1)
    inner = properties.get("inner", "")
    if len(inner) and escape:
        codes = { "&": "&amp;", '"': "&quot;", "'": "&apos;", "<": "&lt;", ">": "&gt;" }
        inner = "".join([codes.get(c, c) for c in inner])

    tag = properties.get("tag", parent)
    datalist = " ".join(formatted)
    begin = f"{tag} {datalist}".strip()
    if (html5 is None):
        return ""
    
    config = html5.get(tag, {})
    closed = config.get("closed", True)
    if closed:
        return f"<{begin}>{inner}</{tag}>"
    return f"<{begin} />"

def _decode_ftml(ftml):
    # "div #id.class1.class2.class3 data-var='hello' style='font-size:20px;color:#000;' contenteditable > hello, world!"
    
    properties = {}
    temp = list(ftml.split(">"))
    ftml = temp[0].strip()
    
    child = None
    if len(temp) == 2:
        child = temp[1].strip()
        properties["inner"] = child
    
    if not len(ftml):
        if child is None:
            return {}
    
    # shlex workaround
    ftml = re.sub("\\\\'", "&apos;", ftml)
    if (ftml.count("'")%2):
        # this might not throw an error even if the string is truly malformed.
        print("Woshi: Check unescaped single-quotes on the abstracted HTML string.\n  " \
            "Consider replacing each of the extra single-quotes with \\\\' and run again.")
        return

    rules = {}
    classes = []
    attributes = {}
    parts = list(shlex.split(ftml))
    for part in parts:
        part = part.strip()
        if len(part):
            if part[0] in ("#", "."):
                class_names = part.split(".")
                for name in class_names:
                    if "#" in name:
                        attributes["id"] = name.replace("#", "")
                    else:
                        classes.append(name.strip())
            else:
                temp = list(part.split("="))
                name, value = temp[0], None
                if not len(name):
                    continue
                
                i = part.find("=")
                if i >= len(name):
                    value = part[i+1:].replace("&apos;", "'")
                
                found = False
                if (html5 is None):
                    continue
                if (name in html5) and (value is None):
                    properties["tag"] = name
                    properties["action"] = "new"
                    continue
                
                config = html5.get(properties.get("tag", "div"), None)        
                if config is None:
                    continue
                
                tag_attributes = config.get("attributes", [])
                found = (name in tag_attributes)
                if not found and (core_attributes is not None):
                    found = (("*global" in tag_attributes) and (name in core_attributes))
                if not found:
                    events = config.get("events", event_handlers)
                    if (events is not None) and (name is not None):
                        found = (name in events)

                if not found:
                    if name in ("escape", "static", "cached", "xpath"):
                        rules[name] = 0
                        if value == "1":
                            rules[name] = 1
                        continue
                    if name[0:5] not in ("aria-", "data-"):
                        continue
                if name == "class":
                    for c in value.split(" "):
                        c = c.strip()
                        if len(c) and (c not in classes):
                            classes.append(c)
                elif name == "style":
                    if (css3_properties is None):
                        continue
                    styling = []
                    for style in value.split(";"):
                        temp = style.split(":")
                        if len(temp) != 2:
                            value = ""
                            continue
                        if temp[0].strip() in css3_properties:
                            styling.append(style)
                    value = ""
                    if len(styling):
                        value = ";".join(styling)
                else:
                    attributes[name] = value
    if len(classes):
        attributes["class"] = " ".join(classes)
    if len(attributes):
        properties["attributes"] = attributes
    if len(rules):
        properties["rules"] = rules
    return properties

def _new_folders(filepath):
    try:
        if not os.path.exists(filepath):
            return os.makedirs(filepath)
    except:
        return False

def _new_file(filepath, content):
    with open(filepath, "w+") as f:
        f.write(content)

##################################################
# constants                                      #
##################################################

html5 = { "a": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global", "download", "href", "hreflang", "media", "ping", "referrerpolicy", "rel", "target", "type"]}, "abbr": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global"]}, "address": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global"]}, "area": { "parent": ["map"], "attributes": ["*global", "alt", "coords", "download", "href", "hreflang", "media", "referrerpolicy", "rel", "shape", "target", "type"]}, "article": { "parent": ["*body"], "attributes": ["*global"]}, "aside": { "parent": ["*body"], "attributes": ["*global"]}, "audio": { "parent": ["*body"], "allowed": ["source"], "attributes": ["*global", "autoplay", "controls", "loop", "muted", "preload", "src"]}, "b": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global"]}, "base": { "parent": ["head"], "closed": False, "attributes": ["*global", "href", "target"], "limit": 1 }, "bdi": { "parent": ["*body", "div", "p", "span", "li"], "attributes": ["*global"]}, "bdo": { "parent": ["*body", "div", "p", "span", "li"], "attributes": ["*global"]}, "blockquote": { "parent": ["*body"], "attributes": ["*global", "cite"]}, "body": { "parent": "html", "attributes": ["*global"], "limit": 1 }, "br": { "parent": ["*body", "div", "p", "span"], "closed": False, "attributes": ["*global"]}, "button": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global", "autofocus", "disabled", "form", "formaction", "formenctype", "formmethod", "formnovalidate", "formtarget", "name", "type", "value"]}, "canvas": { "parent": ["*body"], "attributes": ["*global", "height", "width"]}, "caption": { "parent": ["table"], "attributes": ["*global"]}, "cite": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global"]}, "code": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global"]}, "col": { "parent": ["colgroup"], "attributes": ["*global", "span"]}, "colgroup": { "parent": ["table"], "allow": ["col"], "attributes": ["*global", "span"]}, "command": { "parent": ["*body", "li"], "attributes": ["*global", "value"]}, "datalist": { "parent": ["*body"], "allow": ["option"], "attributes": ["*global"]}, "dd": { "parent": ["dl"], "attributes": ["*global"]}, "del": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global", "cite", "datetime"]}, "details": { "parent": ["*body"], "attributes": ["*global", "open"]}, "dfn": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global"]}, "dialog": { "parent": ["*body"], "attributes": ["*global", "open"]}, "div": { "parent": ["*body"], "attributes": ["*global"]}, "dl": { "parent": ["*body"], "allowed": ["dt", "dd"], "attributes": ["*global"]}, "dt": { "parent": ["dl"], "attributes": ["*global"]}, "em": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global"]}, "embed": { "parent": ["*body"], "attributes": ["*global", "type", "src", "width", "height"]}, "fieldset": { "parent": ["*body", "form"], "attributes": ["*global", "form", "name", "disabled"]}, "figcaption": { "parent": ["figure"], "attributes": ["*global"]}, "figure": { "parent": ["*body"], "attributes": ["*global"]}, "footer": { "parent": ["body"], "attributes": ["*global"]}, "form": { "parent": ["*body"], "attributes": ["*global", "accept-charset", "action", "autocomplete", "enctype", "method", "name", "novalidate", "rel", "target"]}, "h1": { "parent": ["*body"], "attributes": ["*global"]}, "h2": { "parent": ["*body"], "attributes": ["*global"]}, "h3": { "parent": ["*body"], "attributes": ["*global"]}, "h4": { "parent": ["*body"], "attributes": ["*global"]}, "h5": { "parent": ["*body"], "attributes": ["*global"]}, "h6": { "parent": ["*body"], "attributes": ["*global"]}, "head": { "parent": ["html"], "allowed": ["title", "style", "base", "link", "meta", "script", "noscript"], "events": None, "limit": 1 }, "header": { "parent": ["*body"], "attributes": ["*global"]}, "hr": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global"]}, "html": { "root": True, "attributes": ["*global", "lang", "manifest", "xmlns"], "allowed": ["head", "body"], "events": None, "limit": 1 }, "i": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global"]}, "iframe": { "parent": ["*body"], "attributes": ["*global", "allow", "allowfullscreen", "allowpaymentrequest", "height", "loading", "name", "referrerpolicy", "sandbox", "src", "srcdoc", "width"]}, "img": { "parent": ["*body"], "closed": False, "attributes": ["*global", "alt", "crossorigin", "height", "ismap", "loading", "longdesc", "referrerpolicy", "sizes", "src", "srcset", "usemap", "width"]}, "input": { "parent": ["*body"], "closed": False, "attributes": ["*global", "accept", "alt", "autocomplete", "autofocus", "checked", "dirname", "disabled", "form", "formaction", "formenctype", "formmethod", "formnovalidate", "formtarget", "height", "list", "max", "maxlength", "min", "minlength", "multiple", "name", "pattern", "placeholder", "readonly", "required", "size", "src", "step", "type", "value", "width"]}, "ins": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global", "site", "datetime"]}, "kbd": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global"]}, "label": { "parent": ["*body"], "attributes": ["*global"]}, "legend": { "parent": ["fieldset"], "attributes": ["*global"]}, "li": { "parent": ["ul", "ol", "menu"], "attributes": ["*global", "value"]}, "link": { "parent": ["head"], "closed": False, "attributes": ["*global", "crossorigin", "href", "rel", "media", "hreflang", "type", "sizes", "title", "referrerpolicy"]}, "main": { "parent": ["body"], "attributes": ["*global"], "limit": 1 }, "map": { "parent": ["*body"], "allowed": ["area"], "attributes": ["*global", "name"]}, "mark": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global"]}, "meta": { "parent": ["head"], "closed": False, "attributes": ["charset", "content", "http-equiv", "name"], "events": None }, "meter": { "parent": ["*body"], "attributes": ["*global", "id", "form", "low", "high", "min", "max", "optimum", "value"]}, "nav": { "parent": ["body"], "attributes": ["*global"]}, "noscript": { "parent": ["head", "body"], "attributes": ["*global"], "events": None }, "object": { "parent": ["*body"], "attributes": ["*global", "data", "form", "height", "name", "type", "typemustmatch", "usemap", "width"]}, "ol": { "parent": ["*body"], "allowed": ["li"], "attributes": ["*global", "reverse", "start", "type"]}, "optgroup": { "parent": ["select"], "attributes": ["*global", "disabled", "label"]}, "option": { "parent": ["select", "optgroup", "datalist"], "attributes": ["*global", "disabled", "label", "selected", "value"]}, "output": { "parent": ["form"], "attributes": ["*global", "for", "form", "name"]}, "p": { "parent": ["*body"], "attributes": ["*global"]}, "param": { "parent": ["object"], "attributes": ["*global", "name", "value"]}, "picture": { "parent": ["*body"], "allowed": ["source"], "attributes": ["*global", "width", "height", "controls"]}, "pre": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global", "cite"]}, "progress": { "attributes": ["*global", "max", "value"]}, "q": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global", "cite"]}, "rp": { "parent": ["ruby"], "attributes": ["*global"]}, "rt": { "parent": ["ruby"], "attributes": ["*global"]}, "ruby": { "parent": ["*body", "div", "p", "span"], "allowed": ["rt", "rp"], "attributes": ["*global"]}, "s": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global"]}, "samp": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global"]}, "script": { "parent": ["head", "body"], "attributes": ["*global", "async", "crossorigin", "defer", "integrity", "nomodule", "referrerpolicy", "src", "type"]}, "section": { "parent": ["*body"], "attributes": ["*global"]}, "select": { "parent": ["*body"], "allowed": ["optgroup ", "option"], "attributes": ["*global", "autofocus", "disabled", "form", "multiple", "name", "required", "size"]}, "small": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global"]}, "source": { "parent": ["audio", "picture", "video"], "attributes": ["media", "src", "srcset", "type"], "events": None }, "span": { "parent": ["*body"], "attributes": ["*global"]}, "strike": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global"]}, "strong": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global"]}, "style": { "parent": ["head", "body"], "attributes": ["*global", "media", "type"]}, "sub": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global"]}, "summary": { "parent": ["details"], "attributes": ["*global"]}, "sup": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global"]}, "svg": { "parent": ["*body"], "attributes": ["width", "height"], "events": None }, "table": { "parent": ["*body"], "allowed": ["caption", "colgroup", "thead", "tbody", "tfoot"], "events": None }, "tbody": { "parent": ["table"], "allowed": ["tr"], "events": None, "limit": 1 }, "td": { "parent": ["tr"], "attributes": ["*global", "colspan", "headers", "rowspan"]}, "template": { "parent": ["*body"], "attributes": ["*global"]}, "textarea": { "parent": ["*body"], "attributes": ["*global", "autofocus", "cols", "dirname", "disabled", "form", "maxlength", "name", "placeholder", "readonly", "required", "rows", "wrap"]}, "tfoot": { "parent": ["table"], "allowed": ["tr"], "events": None, "limit": 1 }, "th": { "parent": ["table", "tr"], "attributes": ["*global", "abbr", "colspan", "headers", "rowspan", "scope"]}, "thead": { "parent": ["table"], "allowed": ["tr"], "events": None, "limit": 1 }, "time": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global", "datetime"]}, "title": { "parent": ["head"], "attributes": ["*global"], "max-string": 50, "events": None, "limit": 1 }, "tr": { "parent": ["table", "thead", "tbody"], "allowed": ["th", "td"], "attributes": ["*global"]}, "track": { "parent": ["audio", "video"], "attributes": ["default", "src", "kind", "srclang", "label"], "events": None }, "u": { "parent": ["*body", "div", "p", "span"], "attributes": ["class"], "events": None }, "ul": { "parent": ["*body"], "allowed": ["li"], "attributes": ["*global"]}, "var": { "parent": ["*body", "div", "p", "span"], "attributes": ["*global"]}, "video": { "parent": ["*body"], "allowed": ["source"], "attributes": ["*global", "width", "height", "controls"]}, "wbr": { "parent": ["*body", "div", "p", "span"], "closed": False, "attributes": ["*global"]} }

core_attributes = [ "accesskey", "class", "contenteditable", "contextmenu", "dir", "draggable", "hidden", "id", "lang", "spellcheck", "style", "tabindex", "title"]

event_handlers = [ "onabort", "onblur", "oncanplay", "oncanplaythrough", "onchange", "onclick", "oncontextmenu", "ondblclick", "ondrag", "ondragend", "ondragenter", "ondragleave", "ondragover", "ondragstart", "ondrop", "ondurationchange", "onemptied", "onended", "onerror", "onfocus", "onformchange", "onforminput", "oninput", "oninvalid", "onkeydown", "onkeypress", "onkeyup", "onload", "onloadeddata", "onloadedmetadata", "onloadstart", "onmousedown", "onmousemove", "onmouseout", "onmouseover", "onmouseup", "onmousewheel", "onpause", "onplay", "onplaying", "onprogress", "onratechange", "onreadystatechange", "onscroll", "onseeked", "onseeking", "onselect", "onshow", "onstalled", "onsubmit", "onsuspend", "ontimeupdate", "onvolumechange", "onwaiting"]

css3_properties = [ "align-content", "align-items", "align-self", "animation", "animation-delay", "animation-direction", "animation-duration", "animation-fill-mode", "animation-iteration-count", "animation-name", "animation-play-state", "animation-timing-function", "backface-visibility", "background", "background-attachment", "background-clip", "background-color", "background-image", "background-origin", "background-position", "background-repeat", "background-size", "border", "border-bottom", "border-bottom-color", "border-bottom-left-radius", "border-bottom-right-radius", "border-bottom-css", "border-bottom-width", "border-collapse", "border-color", "border-image", "border-image-outset", "border-image-repeat", "border-image-slice", "border-image-source", "border-image-width", "border-left", "border-left-color", "border-left-css", "border-left-width", "border-radius", "border-right", "border-right-color", "border-right-css", "border-right-width", "border-spacing", "border-css", "border-top", "border-top-color", "border-top-left-radius", "border-top-right-radius", "border-top-css", "border-top-width", "border-width", "bottom", "box-shadow", "box-sizing", "caption-side", "clear", "clip", "color", "column-count", "column-fill", "column-gap", "column-rule", "column-rule-color", "column-rule-css", "column-rule-width", "column-span", "column-width", "columns", "content", "counter-increment", "counter-reset", "cursor", "direction", "display", "empty-cells", "flex", "flex-basis", "flex-direction", "flex-flow", "flex-grow", "flex-shrink", "flex-wrap", "float", "font", "font-family", "font-size", "font-size-adjust", "font-stretch", "font-css", "font-variant", "font-weight", "height", "justify-content", "left", "letter-spacing", "line-height", "list-css", "list-css-image", "list-css-position", "list-css-type", "margin", "margin-bottom", "margin-left", "margin-right", "margin-top", "max-height", "max-width", "min-height", "min-width", "opacity", "order", "outline", "outline-color", "outline-offset", "outline-css", "outline-width", "overflow", "overflow-x", "overflow-y", "padding", "padding-bottom", "padding-left", "padding-right", "padding-top", "page-break-after", "page-break-before", "page-break-inside", "perspective", "perspective-origin", "position", "quotes", "resize", "right", "tab-size", "table-layout", "text-align", "text-align-last", "text-decoration", "text-decoration-color", "text-decoration-line", "text-decoration-css", "text-indent", "text-justify", "text-overflow", "text-shadow", "text-transform", "top", "transform", "transform-origin", "transform-css", "transition", "transition-delay", "transition-duration", "transition-property", "transition-timing-function", "vertical-align", "visibility", "white-space", "width", "word-break", "word-spacing", "word-wrap", "z-index"]