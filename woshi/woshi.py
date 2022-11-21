"""
    (c) 2022 Rodney Maniego Jr.
    Woshi
"""

import threading
from .constants import (
    HTML5,
    OPEN_TAGS,
    CSS3,
    ATTRIBUTES,
    HANDLERS,
    RE_HTML_COMPLEX,
    RE_HTML_NEWLINES,
    RE_CSS3_SELECTORS,
    RE_WML_DBL_QUOTES,
    RE_WML_APOSTROPHE,
    RE_WML_ID,
    RE_WML_CLASS,
    RE_WML_QUOTES,
    RE_PATH_TAG,
    RE_PATH_ID,
    RE_PATH_CLASS,
)


class Woshi:
    def __init__(self, html=None, filepath=None, strict=True):
        self._filepath = filepath
        self._html = _parse_to_html(html)
        self._lock = threading.RLock()

        if not isinstance(strict, bool):
            raise WoshiException("`strict` must be `True` or `False` only.")
        self._strict = strict

    def __setitem__(self, path, wml):
        with self._lock:
            path = path.strip().lower()
            if not path:
                WoshiException("`path` must be a string")
            wml = wml.strip()
            self._html = _attach_wml(self._html, path, wml, self._strict)

    def append(self, path, html):
        self.__setitem__(path, html)

    def __getitem__(self, path):
        with self._lock:
            return _find_matches(self._html, path)

    def get(self, path):
        return self.__getitem__(path)

    def build(self):
        return self._html.replace(" >", ">")

    def save(self, filepath=None):
        with self._lock:
            if filepath is not None:
                self._filepath = filepath
            if self._filepath is not None:
                self._filepath = filepath.strip()
                with open(self._filepath, "w+", encoding="utf-8") as f:
                    f.write(self.build())


def _validate_path(path):
    """Check if selectors conform to CSS3 standards."""
    if RE_CSS3_SELECTORS.sub("", path):
        raise WoshiException("`path` only accepts valid CSS3 selectors.")
    # https://dev.to/af/xpath-vs-css-selector-what-is-going-on-with-these-two-4i7g
    # - all p elements
    # - element by ID
    # - element by Class
    # - others, pending


def _parse_path(path):
    """ """
    tag = ""
    search = ""
    selector = ""
    attribute = ""
    if not RE_PATH_TAG.sub("", path):
        tag = path
        search = "<" + path
        selector = "tag"
    elif not RE_PATH_ID.sub("", path):
        tag, search = path.split("#")
        selector = "id"
        attribute = "id="
    elif not RE_PATH_CLASS.sub("", path):
        tag, search = path.split(".")
        selector = "class"
        attribute = "class="
    return (tag, search, selector, attribute)


def _attach_wml(html, path, wml, strict):
    """Update HTML with new attributes or path."""
    _validate_path(path)

    decoded = wml
    if decoded[0] != "<":
        decoded = _decode_wml(decoded, strict)
    append = int((decoded[0] == "<"))

    tag, search, selector, attribute = _parse_path(path)
    attribute_width = len(attribute)

    if not selector:
        raise WoshiException("Complex CSS3 selectors are currently unsupported.")

    if not search:
        return html

    next = html
    formatted = ""
    width = len(search)
    while next:
        if not append:
            # this will append the attributes
            # to the selected element/s
            if selector == "tag":
                # find opening bracket:
                l = _lfind(next, search, strict=False)
                if l == -1:
                    formatted += next
                    break
                # find closing bracket:
                remaining = next[l + width :]
                r = _lfind(remaining, ">")
                closing = [">", " />"][(remaining[r - 1] == "/")]
                # concatenate left + decoded wml
                formatted += next[: l + width] + " " + decoded + closing
                # proceed to remaining html
                next = remaining[r + 1 :]
                continue
            # find element by id, class
            # find selector attribute:
            l = _lfind(next, attribute, strict=False)
            if l == -1:
                formatted += next
                break
            # get value of attribute
            remaining = next[l + attribute_width :]
            quote = remaining[0]
            r = _lfind(remaining, quote)
            if search not in remaining[1:r]:
                # if not found,
                # proceed to next element
                r = _lfind(next, ">")
                formatted += next[: r + 1]
                next = next[r + 1 :]
                continue
            # find closing tag:
            r = _lfind(remaining, ">")
            closing = [">", " />"][(remaining[r - 1] == "/")]
            # concatenate left + decoded wml
            formatted += next[: l - 1] + " " + decoded + closing
            # proceed to remaining html
            next = remaining[r + 1 :]
            if selector == "id":
                formatted += next
                break
            continue
        # append child
        if selector == "tag":
            # find opening bracket:
            l = _lfind(next, search, strict=False)
            if l == -1:
                formatted += next
                break
            # find closing bracket:
            r = _lfind(next[l:], ">")
            if tag in OPEN_TAGS:
                formatted += next[: r + 1]
                next = next[r + 1 :]
                continue
            # concatenate decoded wml after the last child
            offset = _find_last_child(next[l + r + 1 :], tag)
            formatted += next[: offset + l + r + 1] + decoded
            # proceed to remaining html
            next = next[offset + l + r + 1 :]
            continue
        # append by element id/class
        l = _lfind(next, attribute, strict=False)
        if l == -1:
            formatted += next
            break
        # get the attribute value
        # attribute='value' <--
        quote = next[l + attribute_width :][0]
        remaining = next[l + attribute_width :]
        r = _lfind(remaining[1:], quote)
        if search not in remaining[1 : r + 1]:
            # if not found, proceed to next element
            # get the whole tag: <start a='b'> OR </end>
            r = _lfind(next, ">")
            formatted += next[: r + 1]
            next = next[r + 1 :]
            continue

        # locate origin and tag having the attribute
        # if the attribute='value' has been found
        # get all elements on the left of the attribute value
        origin = next[:l]
        offset = len(origin)
        # find tag uses rfind `<` to get:
        # `span` in "</div></div><span"
        tag = _find_tag(origin)
        # on the characters to the right of the attribute,
        # find the index of the clsoing angled bracket
        r = _lfind(next[l:], ">") + 1
        # use the l (left) and r (right) index to get
        # all tag from start to the searched element:
        # example: </div></div><span attribute='value'>
        formatted += next[: offset + r]

        # concatenate decoded wml
        if tag in OPEN_TAGS:
            # tag is not a 'closed' tag,
            # append it immediately after the end
            # of the element
            formatted += decoded
            next = next[offset + r + 1 :]
            continue

        # concatenate after the last child
        siblings = next[offset + r :]
        offset = _find_last_child(siblings, tag)
        formatted += siblings[:offset] + decoded
        # proceed to remaining html
        next = siblings[offset:]
    return formatted


def _find_matches(html, path):
    print(html, path)
    _validate_path(path)
    tag, search, selector, attribute = _parse_path(path)
    attribute_width = len(attribute)
    if selector == "tag":
        # find opening bracket:
        l = _lfind(html, search)
        # find closing bracket:
        r = _lfind(html[l:], ">")
        if tag in OPEN_TAGS:
            return html[l + r]
        # find children until closing tag
        offset = _find_last_child(html[l + r + 1 :], tag)
        return html[l : offset + l + r + 1] + f"</{tag}>"

    while html:
        # append by element id/class
        l = _lfind(html, attribute)
        # get value of attribute
        quote = html[l + attribute_width :][0]
        remaining = html[l + attribute_width :]
        r = _lfind(remaining[1:], quote)
        if search not in remaining[1 : r + 1]:
            # if not found,
            # proceed to next element
            r = _lfind(remaining, ">")
            html = remaining[r + 1 :]
            continue
        # locate origin and tag having the attribute
        origin = html[:l]
        offset = len(origin)
        l = _rfind(origin, "<")
        r = _lfind(html[l:], ">") + 1

        # concatenate decoded wml
        tag = _find_tag(origin)
        if tag in OPEN_TAGS:
            return html[offset + r + 1 :]

        # concatenate after the last child
        siblings = html[l+r:]
        offset = _find_last_child(siblings, tag)
        return html[l:l+r] + siblings[:offset] + f"</{tag}>"
    return ""


def _get_tag(html):
    """Get tag searching from leftmost index."""
    elements = list(RE_HTML_COMPLEX.findall(html))
    if elements:
        element = elements[0]
        if html[: len(element)] == element:
            i = _lfind(html, "<")
            return html[i + 1 :].split(" ")[0]
    l = _lfind(html, "<")
    r = _lfind(html[l:], ">")
    return html[l + 1 : l + r]


def _find_tag(html):
    """Find tag searching from rightmost index."""
    l = _rfind(html, "<")
    r = _lfind(html[l:], " ")
    return html[l + 1 : l + r]


def _lfind(html, search, strict=True):
    i = html.find(search)
    if strict and i == -1:
        raise WoshiException("Unable to search key in HTML string.")
    return i


def _rfind(html, search, strict=True):
    i = html.rfind(search)
    if strict and i == -1:
        raise WoshiException("Unable to search key in HTML string.")
    return i


def _find_last_child(html, tag):
    i = 0
    tags = [tag]
    length = len(html)
    while i < length:
        r = _lfind(html[i:], "<", strict=False)
        if r == -1:
            break
        offset = _lfind(html[i + r :], ">") + 1
        t = _get_tag(html[i + r :])
        if t[0] == "/":
            if tags[-1] == t[1:]:
                tags = tags[:-1]
            if not tags:
                return i + r
            i += offset
            continue
        if t not in OPEN_TAGS:
            tags.append(t)
        i += offset
    return i


def _decode_wml(wml, strict):
    # "div #id.class1.class2.class3 data-var='hello' style='font-size:20px;color:#000;' contenteditable > hello, world!"

    if not wml:
        return wml

    index = len(wml)
    if ">" in wml:
        index = wml.find(">")
    content = wml[index + 1 :].strip()
    wml = wml[:index].strip()

    # convert escaped quotes to html entities
    wml = RE_WML_DBL_QUOTES.sub("&#34;", wml)
    wml = RE_WML_APOSTROPHE.sub("&#39;", wml)
    wml += " "

    tag = ""
    eid = ""
    classes = []
    append = False
    config = {}

    rules = {}
    quotes = ""
    property = ""
    properties = []
    tag_attributes = ""
    for i in range(len(wml)):
        character = wml[i]
        if character == " " and not quotes:
            if property:
                if not tag:
                    append = "=" not in property
                    if append:
                        tag, eid, classes = _break_tag_identity(property)
                        if strict and tag not in HTML5:
                            if not tag:
                                decoded = eid
                                if classes:
                                    decoded += (
                                        " class='" + " ".join(list(set(classes))) + "'"
                                    )
                                return decoded.strip()
                            raise WoshiException("No HTML5 tag found on WML text.")
                        config = HTML5.get(tag, {})
                        tag_attributes = config.get("attributes", "")
                        property = ""
                        continue
                if property[0] in "#.":
                    _, eid, c = _break_tag_identity(property)
                    classes.extend(c)
                    property = ""
                    continue
                if "=" in property:
                    name, value = property.split("=")
                    if value:
                        value = RE_WML_QUOTES.sub("", value)
                        found = (
                            (name in tag_attributes)
                            or (("*global" in tag_attributes) and (name in ATTRIBUTES))
                            or (name in HANDLERS)
                        )
                        property = ""
                        if not found:
                            if name in ("escape", "static", "cached"):
                                rules[name] = int(value)
                                continue
                        if name == "id":
                            eid = f"id='{value}'"
                            continue
                        if name == "class":
                            classes.append(value)
                            continue
                        if strict and name == "style":
                            styling = []
                            for style in value.split(";"):
                                k, v = style.split(":")
                                if v and k.strip() in CSS3:
                                    styling.append(style)
                            if len(styling):
                                value = ";".join(styling)
                        properties.append([name, value])
                        continue
                properties.append([property])
            property = ""
            continue
        property += character
        if character in ("'\""):
            if quotes:
                if quotes[-1] == character:
                    quotes = quotes[-1]
                    continue
            quotes += character
            continue

    # format all attributes
    attributes = []
    if eid:
        attributes.append(eid)
    if classes:
        attributes.append("class='" + " ".join(list(set(classes))) + "'")
    if properties:
        for name, value in properties:
            if not value:
                attributes.append(name)
                continue
            if tag in ("link", "img", "script"):
                if (name in ("href", "src")) and not rules.get("cached", 1):
                    if "?" in value:
                        value += "&t=" + str(int(time.time()))
                    else:
                        value += "?t=" + str(int(time.time()))
                if rules.get("static", 0):
                    value = "{{ url_for('static', filename='" + value + "') }}"
            attributes.append((name + "='" + value + "'"))

    if not append:
        return " ".join(attributes)

    begin = tag
    if attributes:
        begin += " " + " ".join(attributes)

    # format into a valid strict tag
    if tag not in OPEN_TAGS:
        if content and rules.get("escape", 0):
            content = "".join([HTML_ENTITIES.get(c, c) for c in content])
        return f"<{begin}>{content}</{tag}>"
    return f"<{begin} />"


def _break_tag_identity(tag):
    # https://www.w3.org/TR/selectors-3/
    eid = ""
    classes = []
    if "#" in tag:
        hashid = list(RE_WML_ID.findall(tag))[0]
        eid = "id='" + hashid[1:] + "'"
        tag = tag.replace(hashid, "")
    if "." in tag:
        for item in list(RE_WML_CLASS.findall(tag)):
            classes.append(item[1:])
            tag = tag.replace(item, "")
    return tag, eid, classes


def _parse_to_html(html):
    if html is None:
        return "<!DOCTYPE html><html><head></head><body></body></html>"
    if isinstance(html, bytes):
        html = str(html, "utf-8")
    if isinstance(html, str):
        return RE_HTML_NEWLINES.sub(">", html)
    raise WoshiException("`html` must be in string format.")


class WoshiException(Exception):
    """Custom Woshi Exception.

    :param message: a valid string
    """

    def __init__(self, message):
        super().__init__(message)
