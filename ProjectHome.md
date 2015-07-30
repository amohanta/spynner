**The development of spynner has been moved to [github](https://github.com/makinacorpus/spynner).**

# Spynner #

Spynner is a stateful programmatic web browser module for Python with
Javascript/AJAX support based upon the QtWebKit framework.

```
import spynner

browser = spynner.Browser()
browser.load("http://www.wordreference.com")
browser.runjs("console.log('I can run Javascript!')")
browser.runjs("_jQuery('div').css('border', 'solid red')") # and jQuery!
browser.select("#esen")
browser.fill("input[name=enit]", "hola")
browser.click("input[name=b]")
browser.wait_page_load()
print browser.url, len(browser.html)
browser.close()
```

License: [MIT](http://www.opensource.org/licenses/mit-license.php)