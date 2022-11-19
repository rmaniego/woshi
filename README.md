# woshi
On-the-go HTML Abstraction and Generator for Python.

You're prototyping the next big thing and definitely writing the perfect HTML file is not on the priority.

**Woshi** lets you create HTML documents on the go and inside your Python scripts. It is built on top of **lxml.html** plus with another level of abstraction, so you can code with no trouble of messing up with closing tags--it is so quick and easy!

Here's a sample syntax:
```python
page["tag#id"] = "tag #id.class property='10' > inner text"
```
And scroll down below for more examples.

## Official Release
Current version is 2.0, but more updates are coming soon. Compatible with Python 3.9 or later.

`pip install woshi -U`


## Usage
**Import Package**
```python
from woshi import Woshi
```

**Initialization**
```python
page = Woshi()

# initializing with a valid HTML text
page = Woshi("<!DOCTYPE html>...")

# setting up filename
page = Woshi(filepath="home.html")
```

**Creating elements with an inner text**
```python
page["head"] = "title > Woshi v1.0"
```

**Creating other elements**
Basically, you set the parent selector to append the new element.
```python
# create container box
page["body"] = "div #content"
page["#content"] = "div #box.container.light"

# create the popup text
page["#box"] = "div #title.header > Woshi"
page["#box"] = "div .message data-default='Lorem ipsum...' > Hello, world!"

# populate the action buttons
page["#box"] = "div #action.btn-list"
page["#action"] = "button #btn1.btn.btn-no style='background-color:#b22222;color:#fff;' > CLOSE"
page["#action"] = "button #btn2.btn.btn-maybe > LATER"
```

**Setting Properties**
```python
page["html"] = "lang=en"
page["body"] = "#canvas"
```

**Yield all matches**
```python
print(page["button"])
```

**Save to HTML file**
```python
page.save()
page.save("newFile.html")
```
