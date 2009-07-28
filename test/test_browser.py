#!/usr/bin/python

# Copyright (c) Arnau Sanchez <tokland@gmail.com>

# This script is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>

import os
import sys
import signal
import unittest
import threading
from StringIO import StringIO

import spynner
import webserver
             
TESTDIR = os.path.dirname(__file__)
TESTING_SERVER_PORT = 9876 
           
def get_url(path):
    return "http://localhost:%s" % TESTING_SERVER_PORT + path

def get_file_path(*path):
    return os.path.join(TESTDIR, "fixtures", *path)

def start_threaded_server(port):
    server = webserver.get_server('', port, get_file_path())
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    return server, thread

class SpynnerBrowserTest(unittest.TestCase):    
    def setUp(self):
        self.debugoutput = StringIO()
        self.browser = spynner.Browser(debug_level=spynner.DEBUG)
        #self.browser.create_webview(); self.browser.show()
        self.browser.debug_stream = self.debugoutput
        self.browser.load(get_url("/test1.html"))

    def tearDown(self):
        self.browser.close()

    def get_debug(self):
        self.debugoutput.seek(0)
        return self.debugoutput.read()
        
    # Tests
    
    def test_init_with_webview(self):
        self.browser.create_webview()
        html = self.browser.load(get_url("/test1.html"))
        self.browser.webview.show = lambda *args: None
        self.browser.show()
        self.browser.wait(0.01)
        self.browser.hide()
        self.browser.destroy_webview()        

    def test_load_should_return_status_boolean(self):
        self.assertTrue(self.browser.load(get_url("/test1.html")))
        self.assertFalse(self.browser.load("wrong://this-cannot-work"))

    def test_html(self):
        self.assertTrue("Test1 HTML" in self.browser.html)

    def test_get_url(self):
        self.assertEqual(get_url("/test1.html"), self.browser.url)

    def test_wait_page_load(self):
        self.browser.runjs("window.location = '/test2.html'")
        self.browser.wait_page_load(1000)

    def test_wait_page_load_raises_exception_on_timeout(self):
        self.assertRaises(spynner.SpynnerTimeout, 
            self.browser.wait_page_load, 0.1)
        
    def test_click(self):
        self.browser.click("#link")
        self.browser.wait_page_load()
        self.assertEqual(get_url('/test3.html'), self.browser.url)            

    def test_check(self):
        self.browser.check("#check")
        jscode = "jQuery('#check').attr('checked')"
        self.assertTrue(self.browser.runjs(jscode).toPyObject())

    def test_uncheck(self):
        self.browser.uncheck("#check")
        jscode = "jQuery('#check').attr('checked')"
        self.assertFalse(self.browser.runjs(jscode).toPyObject())

    def test_choose(self):
        self.browser.choose("#radio2")
        jscode = "jQuery('#radio2').attr('checked')"
        self.assertTrue(self.browser.runjs(jscode).toPyObject())

    def test_select(self):
        self.browser.select("#select option[value=2]")
        jscode = "jQuery('#option2').attr('selected')"
        self.assertTrue(self.browser.runjs(jscode).toPyObject())

    def test_fill(self):
        self.browser.fill("input[name=user]", "myname")
        self.browser.click("#submit")
        self.browser.wait_page_load()
        self.assertEqual(get_url('/test2.html?user=myname'), 
            self.browser.url)            
                
    def test_runjs(self):
        jscode = "document.getElementById('link').innerHTML = 'hello there!'" 
        self.browser.runjs(jscode)
        self.assertTrue("hello there!" in self.browser.html)

    def test_get_mozilla_cookies(self):
        cookies = self.browser.get_mozilla_cookies()
        self.assertTrue("# Netscape HTTP Cookie File" in cookies)
        self.assertTrue("mycookie" in cookies)
        self.assertTrue("12345" in cookies)

    def test_javascript_console_message(self):
        self.browser.runjs("console.log('hello there!')")
        output = self.get_debug()
        self.assertTrue("Javascript console" in output)
        self.assertTrue("hello there!" in output)        

    def test_javascript_alert(self):
        self.browser.runjs("alert('hello there!')")
        output = self.get_debug()
        self.assertTrue("Javascript alert" in output)
        self.assertTrue("hello there!" in output)        

    def test_download(self):
        data = self.browser.download(get_url('/test2.html'))
        self.assertEqual(open(get_file_path('test2.html')).read(), data)

    def test_download_only_http(self):
        self.assertRaises(spynner.SpynnerError,
            self.browser.download, "ftp://server.com/file.tgz")

    def test_stream_download(self):
        outfd = StringIO()
        self.browser.download(get_url('/test2.html'), outfd=outfd)
        expected_data = open(get_file_path('test2.html')).read()
        self.assertEqual(expected_data, outfd.getvalue())

    def test_get_url_from_path(self):
        self.assertEqual(get_url("/test2.html"), 
            self.browser.get_url_from_path('/test2.html'))
        
    def test_set_url_filter(self):
        def url_filter(operation, url):
            if url == get_url("/test2.html"):
                return False
        self.browser.set_url_filter(url_filter)
        old_html = self.browser.html
        self.browser.load(get_url("/test2.html"))
        self.assertEqual(old_html, self.browser.html)
        
    def test_javascript_confirm(self):
        def confirm_no(url, message):
            return False
        self.browser.set_javascript_confirm_callback(confirm_no)                
        self.browser.click("#link_confirmed")
        self.assertEqual(get_url("/test1.html"), self.browser.url)
        
        def confirm_yes(url, message):
            return True
        self.browser.set_javascript_confirm_callback(confirm_yes)                
        self.browser.click("#link_confirmed")
        self.browser.wait_page_load()
        self.assertEqual(get_url("/test3.html"), self.browser.url)

    def test_javascript_prompt(self):
        def answer(url, message, defaultvalue):
            return "My answer"
        self.browser.set_javascript_prompt_callback(answer)                
        self.browser.click("#link_prompt")
        self.assertTrue("User answer: My answer" in self.get_debug())            

        def cancel_answer(url, message, defaultvalue):
            return
        self.browser.set_javascript_prompt_callback(cancel_answer)                
        self.debugoutput.seek(0)
        self.debugoutput.truncate()
        self.browser.click("#link_prompt")
        self.assertTrue("User answer" not in self.get_debug())            
        
                    
def suite():
    return unittest.TestLoader().loadTestsFromTestCase(SpynnerBrowserTest)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    thread = start_threaded_server(port=TESTING_SERVER_PORT)
    unittest.main()