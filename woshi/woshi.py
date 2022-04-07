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
from xml.dom import minidom
from arkivist import Arkivist
from .constants import html5, core_attributes, event_handlers, css3_properties

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
                if not len(xpath:=xpath.strip()):
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
                    if not len(xpath:=xpath.strip()):
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
                if not len(filepath:=filepath.strip()):
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
                if len((parent_tag:=parent_tag.strip())):
                    return f".//{parent_tag}[@id='{attribute}']"
        elif "." in selector:
            temp = selector.split(".")
            if len(temp) == 2:
                parent_tag, attribute = temp
                if len((parent_tag:=parent_tag.strip())):
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
    if len(id:=properties.get("id", "")):
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
        properties["inner"] = (child:=temp[1].strip())
    
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
        if len(part:=part.strip()):
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
                if not len(name:=name.strip()):
                    continue
                
                if (i:=part.find("=")) >= len(name):
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
                        if len(c:=c.strip()) and c not in classes:
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