# -*- coding: utf-8 -*-
"""
A small program that turns an MBOX file into a stylized 
html file which can be rendered and printed as a PDF.
"""

import sys
from argparse import ArgumentParser
import mailbox
import email.utils
from email.header import Header, decode_header, make_header
from email.utils import parsedate
from email_reply_parser import EmailReplyParser
import quopri, base64
import time
from dateutil import parser
from dateutil.parser import parse
from datetime import date, datetime
from templates import book_template, chapter_template, message_template


class Message(object):
    '''
    Store message data
    '''
    fromm = ""
    date = ""
    subject = ""
    body = ""

    def __init__(self, fromm, date, subject, body):
        self.fromm = fromm
        self.date = date
        self.subject = subject
        self.body = body


class Chapter(object):
    '''
    Define a chapter and corresponding array of messages
    '''

    name = ""

    def __init__(self, name, message):
        self.name = name
        self.messages = []
        self.messages.append(message)


def make_message(fromm, date, subject, body):
    message = Message(fromm, date, subject, body)
    return message


def make_chapter(name, message):
    chapter = Chapter(name, message)
    return chapter


def get_charsets(msg):
    charsets = set({})
    for c in msg.get_charsets():
        if c is not None:
            charsets.update([c])
    return charsets


def handle_error(errmsg, emailmsg,cs):
    print(errmsg)
    print("While decoding ",cs," charset.")
    print("Charsets in email: ",get_charsets(emailmsg))
    print("Subject: ", emailmsg['subject'])
    print("Sender: ", emailmsg['From'])


def get_body_from_email(msg):
    '''
    Extracts txt body from a message
    '''
    body = None
    #Walk through the parts of the email to find the text body.    
    if msg.is_multipart():    
        for part in msg.walk():
            # If part is multipart, walk through the subparts.            
            if part.is_multipart(): 
                for subpart in part.walk():
                    if subpart.get_content_type() == 'text/plain':
                        # Get the subpart payload (i.e the message body)
                        body = subpart.get_payload(decode=True) 
            # Part isn't multipart so get the email body
            elif part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True)
    # If this isn't a multi-part message then get the payload (i.e the message body)
    elif msg.get_content_type() == 'text/plain':
        body = msg.get_payload(decode=True) 

   # No checking done to match the charset with the correct part. 
    for charset in get_charsets(msg):
        try:
            body = body.decode(charset)
        except UnicodeDecodeError:
            handle_error("Unicode Decode Error", msg, charset)
        except AttributeError:
             handle_error("Attribute Error", msg, charset)
    return body    


def extract_date(email):
    date = email.get('Date')
    return parsedate(date)


def get_season(now):
    '''
    Find in which season a certain date is in
    '''
    Y = 2000 # dummy leap year to allow input X-02-29
    seasons = [(0, (date(Y,  1,  1),  date(Y,  3, 20))),
           (1, (date(Y,  3, 21),  date(Y,  6, 20))),
           (2, (date(Y,  6, 21),  date(Y,  9, 22))),
           (3, (date(Y,  9, 23),  date(Y, 12, 20))),
           (4, (date(Y, 12, 21),  date(Y, 12, 31)))]
    if isinstance(now, datetime):
        now = now.date()
    now = now.replace(year=Y)
    return next(season for season, (start, end) in seasons
                if start <= now <= end)

def add_year(d):
    try:
        return d.replace(year = d.year + 1)
    except ValueError:
        return d + (date(d.year + 1 , 1, 1) - date(d.year, 1, 1))


def sub_year(d):
    try:
        return d.replace(year = d.year - 1)
    except ValueError:
        return d + (date(d.year - 1 , 1, 1) - date(d.year, 1, 1))


def make_chapter_name(i_date):
    ssn = get_season(i_date)
    chptr = ""
    if ssn == 0:
        chptr = "Winter '"+ sub_year(i_date).strftime("%y")+" - '"+ i_date.strftime("%y")

    elif ssn == 1:
        chptr = "Spring '" + i_date.strftime("%y")

    elif ssn == 2:
        chptr = "Summer '" + i_date.strftime("%y")

    elif ssn == 3:
        chptr = "Autumn '" + i_date.strftime("%y")

    elif ssn == 4:
        chptr = "Winter '"+ i_date.strftime("%y")+" - '"+ add_year(i_date).strftime("%y")

    return chptr


def is_date(string, fuzzy=False):
    '''
    Return whether the string can be interpreted as a date.
    '''
    try: 
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False


def clean_message(i_body):
    '''
    Cosmetic fixes to message text. Append your own.
    '''
    i_body = i_body.replace("\n\n\n\n", "\n\n")
    i_body = i_body.replace("\n\n\n", "\n\n")
    i_body = i_body.replace("\n", "<br>\n")
    
    i_body_lines = i_body.splitlines()
    if (i_body_lines[-1].startswith("----")):
        i_body_lines[-1] = ""
    if (is_date(i_body_lines[-1], fuzzy=True)):
        i_body_lines[-1] = ""
    i_body = "".join(i_body_lines)
    
    return i_body


def build_book(title, author, mbox_file):
    '''
    main logic
    '''
    #open mbox file, sort messages by date
    mbox = mailbox.mbox(mbox_file)
    sorted_mails = sorted(mbox, key=extract_date)
    mbox.update(enumerate(sorted_mails))
    mbox.flush()
    chapters = [make_chapter("null", make_message("", "", "", ""))]
    #prepare each message
    for message in mbox:
        #subject
        subject, encoding = decode_header(message.get('subject'))[0]
        if encoding==None:
            p_subject = subject
        else:
            p_subject = subject.decode(encoding)
        #from
        p_from = email.utils.parseaddr(message.get('From'))[0]
        #date
        i_date = parser.parse(message.get('Date'))
        p_date = i_date.strftime("%d %b %Y")
        #body
        body = get_body_from_email(message)
        i_body = EmailReplyParser.read(body).fragments[0]._content
        p_body = clean_message(i_body)

        m = make_message(p_from, p_date, p_subject, p_body)
        #insert message in its chapter
        chptr = make_chapter_name(i_date)
        found = False
        for chapter in chapters:
            if chapter.name == chptr:
                chapter.messages.append(m)
                found = True
        if found == False:
            chapters.append(make_chapter(chptr, m))

    #builds html file: insert every message in a template, then compile chapters, finally wrap up book
    s_chapters = ""
    for chapter in chapters:
        if chapter.name != "null":
            s_messages = ""
            for message in chapter.messages:
                #build message, append to messages string
                s_messages += message_template(message.subject, message.fromm, message.date, message.body)
            #build chapter, append messages into chapter string
            s_chapters += chapter_template(chapter.name, s_messages)
    #build book, append chapters in the book string
    s_book = book_template(title, author, s_chapters)

    #write output book file
    fo = open(title+".html", "w")
    fo.write(s_book)
    fo.close()

def main(argv):
    title = ''
    author = ''
    mbox_file = ''


    parser = ArgumentParser()
    parser.add_argument('--title', type=str, required=False)
    parser.add_argument('--author', type=str, required=False)
    parser.add_argument('--mbox', type=str, required=False)

    args = parser.parse_args()

    if not args.title:
        title = "My book"
    else:
        title = args.title

    if not args.author:
        author = "John Doe"
    else:
        author = args.author

    if not args.mbox:
        mbox_file = "sample_mbox"
    else:
        mbox_file = args.mbox


    print ('Title: ', title)
    print ('Author: ', author)
    print ('Mbox: ', mbox_file)
    build_book(title, author, mbox_file)
    sys.exit()

if __name__ == "__main__":
   main(sys.argv[1:])