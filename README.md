# woshi
On-the-go HTML Abstraction and Generator for Python.

You're protoyping the next big thing and definitely writing the perfect HTML file is not on the priority.

**Woshi** let's you create HTML documents on the go and inside your Python scripts. It is built on top of **lxml.html** plus with another level of abstraction, so you can code with no trouble of messing up with closing tags--it is so quick and easy!

Here's a sample syntax:
```python
page["tag#id"] = "tag #id.class property='10' > inner text"
```
And scroll down below for more examples.

## Official Release
**Woshi** can now be used on your Python projects through PyPi by running pip command on a Python-ready environment.

`pip install -U woshi`

Current version is 1.0, but more updates are coming soon.

This is compatible with Python 3.9+, but will require other third-party libraries during installation.


## Usage
**Import Package**
```python
from woshi import Woshi
```

**Initialization**
```python
page = Woshi()
page = Woshi("home.html")
```

**Import Package**
```python
page["head"] = "title > Woshi v1.0"
```

**Import Package**
Basically, you set the parent selector to append the new element.
```python
# create container box
page["body"] = "div #content"
page["#content"] = "div #box.container.light"

# create the popup text
page["#box"] = "div #title.header > Woshi"
page["#box"] = "div .message data-default='Lorem impsum...' > Hello, world!"

# populate the action buttons
page["#box"] = "div #action.btn-list"
page["#action"] = "button #btn1.btn.btn-no style='background-color:#b22222;color:#fff;' > CLOSE"
page["#action"] = "button #btn2.btn.btn-maybe > LATER"

# using lxml xpath
page[".//div[@id='action']"] = "button #btn3.btn.btn-yes > CONTINUE"
```

**Setting Properties**
```python
page["html"] = "lang=en" # not yet allowed in lxml
page["body"] = "#canvas"
```

**Yield all matches**
```python
for element in page["button"]:
    print(element.tag)
```

**Yield all matches as HTML string**
```python
for element in page.get("button", to_string=True, to_xml=True):
    print(element)
```

**Save to HTML file**
```python
page.save()
page.save("newFile.html")
```
