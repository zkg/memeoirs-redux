#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memeoirs Redux: Convert MBOX email files to stylized HTML books.

This program processes email correspondence from MBOX files and generates
beautifully formatted HTML books that can be converted to PDF using Prince XML.
"""

import logging
import re
import sys
from argparse import ArgumentParser
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Tuple, Union
import mailbox
import email.utils
from email.header import decode_header
from email.utils import parsedate
from email_reply_parser import EmailReplyParser
from dateutil import parser
from dateutil.parser import parse
from templates import book_template, chapter_template, message_template

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class Message:
    """Store email message data.
    
    Attributes:
        sender: Email sender name
        date: Formatted date string
        subject: Email subject line
        body: Processed email body content
    """

    def __init__(self, sender: str, date: str, subject: str, body: str) -> None:
        self.sender = sender
        self.date = date
        self.subject = subject
        self.body = body
        
    def __repr__(self) -> str:
        return f"Message(sender='{self.sender}', date='{self.date}', subject='{self.subject}')"


class Chapter:
    """Container for messages grouped by seasonal periods.
    
    Attributes:
        name: Chapter name (e.g., "Spring '23")
        messages: List of Message objects in this chapter
    """

    def __init__(self, name: str, message: Message) -> None:
        self.name = name
        self.messages: List[Message] = [message]
        
    def add_message(self, message: Message) -> None:
        """Add a message to this chapter."""
        self.messages.append(message)
        
    def __repr__(self) -> str:
        return f"Chapter(name='{self.name}', message_count={len(self.messages)})"


def make_message(sender: str, date: str, subject: str, body: str) -> Message:
    """Create a Message instance."""
    return Message(sender, date, subject, body)


def make_chapter(name: str, message: Message) -> Chapter:
    """Create a Chapter instance."""
    return Chapter(name, message)


def get_charsets(msg) -> set:
    """Extract all character sets from an email message."""
    charsets = set()
    for charset in msg.get_charsets():
        if charset is not None:
            charsets.add(charset)
    return charsets


def handle_error(errmsg: str, emailmsg, charset: str) -> None:
    """Log detailed error information for email processing failures."""
    logging.error(f"{errmsg} while decoding {charset} charset")
    logging.error(f"Available charsets: {get_charsets(emailmsg)}")
    logging.error(f"Subject: {emailmsg.get('subject', 'N/A')}")
    logging.error(f"Sender: {emailmsg.get('From', 'N/A')}")


def get_body_from_email(msg) -> Optional[str]:
    """Extract text body from an email message.
    
    Args:
        msg: Email message object
        
    Returns:
        Decoded message body as string, or None if extraction fails
    """
    body = None
    
    # Walk through email parts to find text body
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True)
                break
    elif msg.get_content_type() == 'text/plain':
        body = msg.get_payload(decode=True)
    
    if body is None:
        logging.warning("No plain text body found in email")
        return ""
    
    # Try to decode with available charsets
    if isinstance(body, bytes):
        charsets = get_charsets(msg) or {'utf-8', 'latin-1'}
        for charset in charsets:
            try:
                return body.decode(charset)
            except (UnicodeDecodeError, LookupError) as e:
                handle_error(f"Failed to decode with {charset}: {e}", msg, charset)
                continue
        
        # Fallback to utf-8 with error handling
        try:
            return body.decode('utf-8', errors='replace')
        except Exception as e:
            logging.error(f"Final decode attempt failed: {e}")
            return ""
    
    return body if isinstance(body, str) else str(body)    


def extract_date(email_msg) -> Tuple[int, ...]:
    """Extract and parse date from email header.
    
    Args:
        email_msg: Email message object
        
    Returns:
        Parsed date tuple, or epoch date if parsing fails
    """
    date_str = email_msg.get('Date')
    if not date_str:
        logging.warning("Email has no Date header")
        return (1970, 1, 1, 0, 0, 0, 0, 1, -1)
    
    parsed = parsedate(date_str)
    if parsed is None:
        logging.warning(f"Failed to parse date: {date_str}")
        return (1970, 1, 1, 0, 0, 0, 0, 1, -1)
    
    return parsed


def get_season(now: Union[date, datetime]) -> int:
    """Determine which season a date falls into.
    
    Args:
        now: Date or datetime object
        
    Returns:
        Season number (0=Winter early, 1=Spring, 2=Summer, 3=Autumn, 4=Winter late)
    """
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

def add_year(d: date) -> date:
    """Add one year to a date, handling leap year edge cases."""
    try:
        return d.replace(year=d.year + 1)
    except ValueError:
        # Handle Feb 29 in leap years
        return d + (date(d.year + 1, 1, 1) - date(d.year, 1, 1))


def sub_year(d: date) -> date:
    """Subtract one year from a date, handling leap year edge cases."""
    try:
        return d.replace(year=d.year - 1)
    except ValueError:
        # Handle Feb 29 in leap years
        return d + (date(d.year - 1, 1, 1) - date(d.year, 1, 1))


def make_chapter_name(email_date: Union[date, datetime]) -> str:
    """Generate a seasonal chapter name based on the email date.
    
    Args:
        email_date: Date of the email
        
    Returns:
        Chapter name like "Spring '23" or "Winter '22 - '23"
    """
    season = get_season(email_date)
    year_short = email_date.strftime("%y")
    
    season_names = {
        0: f"Winter '{sub_year(email_date).strftime('%y')} - '{year_short}",
        1: f"Spring '{year_short}",
        2: f"Summer '{year_short}",
        3: f"Autumn '{year_short}",
        4: f"Winter '{year_short} - '{add_year(email_date).strftime('%y')}"
    }
    
    return season_names.get(season, f"Unknown '{year_short}")


def is_date(string: str, fuzzy: bool = False) -> bool:
    """Check if a string can be interpreted as a date.
    
    Args:
        string: String to test
        fuzzy: Whether to use fuzzy parsing
        
    Returns:
        True if string represents a valid date
    """
    if not string or not string.strip():
        return False
        
    try:
        parse(string, fuzzy=fuzzy)
        return True
    except (ValueError, TypeError):
        return False


def is_empty_content(content: str) -> bool:
    """Check if content is effectively empty (only whitespace, breaks, etc).

    Args:
        content: Content string to check (may contain HTML)

    Returns:
        True if content is empty or contains only whitespace/HTML breaks
    """
    if not content:
        return True

    # Remove HTML line breaks and whitespace
    cleaned = content.replace("<br>", "").replace("<br/>", "").replace("<br />", "")
    cleaned = cleaned.strip()

    return len(cleaned) == 0


def has_word_wrapping(message_body: str) -> bool:
    """Detect if message has artificial word-wrapping (consistent line lengths).

    Args:
        message_body: Raw message body text

    Returns:
        True if message appears to have word-wrapping artifacts
    """
    lines = message_body.split("\n")
    # Filter out empty lines
    non_empty_lines = [line for line in lines if line.strip()]

    if len(non_empty_lines) < 5:
        return False  # Not enough data to determine

    # Count various indicators of word-wrapping
    indicators = 0
    total_checks = 0

    # Check 1: Lines ending with lowercase (mid-word/mid-sentence)
    lowercase_ends = sum(1 for line in non_empty_lines
                        if line and line.rstrip()[-1].islower())
    if lowercase_ends / len(non_empty_lines) > 0.4:
        indicators += 1
    total_checks += 1

    # Check 2: Lines with significant length (>20 chars) ending without punctuation
    significant_lines = [line for line in non_empty_lines if len(line) > 20]
    if significant_lines:
        mid_sentence_ends = sum(1 for line in significant_lines
                                if line and line[-1] not in '.!?,;:\'"')
        if mid_sentence_ends / len(significant_lines) > 0.4:
            indicators += 1
        total_checks += 1

    # Check 3: Consistent line lengths (for traditional word-wrapping)
    if len(significant_lines) >= 3:
        line_lengths = [len(line) for line in significant_lines]
        avg_length = sum(line_lengths) / len(line_lengths)
        variance = sum((length - avg_length) ** 2 for length in line_lengths) / len(line_lengths)
        std_dev = variance ** 0.5

        # If average is in typical range AND low variation
        if 50 <= avg_length <= 85 and std_dev < 20:
            indicators += 1
        total_checks += 1

    # If at least 2 out of 3 indicators suggest word-wrapping, treat as wrapped
    return indicators >= 2


def clean_message(message_body: Optional[str]) -> str:
    """Apply cosmetic fixes to message text.

    Args:
        message_body: Raw message body text

    Returns:
        Cleaned and HTML-formatted message body
    """
    if not message_body:
        return ""

    # Normalize excessive line breaks
    cleaned = message_body.replace("\n\n\n\n", "\n\n")
    cleaned = cleaned.replace("\n\n\n", "\n\n")

    # Detect if this message has word-wrapping artifacts
    is_word_wrapped = has_word_wrapping(cleaned)

    if is_word_wrapped:
        # Remove spurious single line breaks (word-wrapping artifacts)
        # Keep double line breaks (paragraph separations) by temporarily replacing them
        cleaned = cleaned.replace("\n\n", "<!PARAGRAPH!>")
        # Remove single line breaks (these are just formatting artifacts)
        cleaned = cleaned.replace("\n", " ")
        # Restore paragraph breaks
        cleaned = cleaned.replace("<!PARAGRAPH!>", "\n\n")
        # Clean up multiple spaces created by line break removal
        cleaned = re.sub(r' {2,}', ' ', cleaned)
        # Convert paragraph breaks to HTML
        cleaned = cleaned.replace("\n\n", "<br>\n<br>\n")
    else:
        # Plain text email - preserve single line breaks
        # Convert single line breaks to HTML
        cleaned = cleaned.replace("\n\n", "<!PARAGRAPH!>")
        cleaned = cleaned.replace("\n", "<br>\n")
        cleaned = cleaned.replace("<!PARAGRAPH!>", "<br>\n<br>\n")

    # Remove common email signatures and date stamps
    lines = cleaned.splitlines()
    if lines:
        # Remove separator lines
        if lines[-1].startswith("----"):
            lines[-1] = ""
        # Remove date signatures
        if lines and is_date(lines[-1], fuzzy=True):
            lines[-1] = ""

    return "\n".join(lines)


def build_book(title: str, author: str, mbox_file: str) -> None:
    """Main logic to process MBOX file and generate HTML book.
    
    Args:
        title: Book title
        author: Book author
        mbox_file: Path to MBOX file
        
    Raises:
        FileNotFoundError: If MBOX file doesn't exist
        ValueError: If MBOX file is invalid
    """
    mbox_path = Path(mbox_file)
    if not mbox_path.exists():
        raise FileNotFoundError(f"MBOX file not found: {mbox_file}")
    
    logging.info(f"Processing MBOX file: {mbox_file}")
    logging.info(f"Generating book: '{title}' by {author}")
    try:
        # Open and sort MBOX file by date
        mbox = mailbox.mbox(mbox_file)
        sorted_mails = sorted(mbox, key=extract_date)
        mbox.update(enumerate(sorted_mails))
        mbox.flush()
    except Exception as e:
        raise ValueError(f"Failed to process MBOX file: {e}") from e
    chapters: List[Chapter] = []
    processed_count = 0
    skipped_count = 0

    # Process each message
    for message in mbox:
        try:
            # Extract and decode subject
            subject_header = message.get('subject', '')
            if subject_header:
                subject_parts = decode_header(subject_header)
                if subject_parts and subject_parts[0]:
                    subject_bytes, encoding = subject_parts[0]
                    if encoding:
                        p_subject = subject_bytes.decode(encoding) if isinstance(subject_bytes, bytes) else str(subject_bytes)
                    else:
                        p_subject = str(subject_bytes)
                else:
                    p_subject = "(No Subject)"
            else:
                p_subject = "(No Subject)"
            
            # Extract sender
            from_header = message.get('From', '')
            p_sender = email.utils.parseaddr(from_header)[0] or "Unknown Sender"
            
            # Parse and format date
            date_header = message.get('Date')
            if date_header:
                try:
                    email_date = parser.parse(date_header)
                    p_date = email_date.strftime("%d %b %Y")
                except (ValueError, TypeError) as e:
                    logging.warning(f"Failed to parse date '{date_header}': {e}")
                    email_date = datetime(1970, 1, 1)
                    p_date = "Unknown Date"
            else:
                email_date = datetime(1970, 1, 1)
                p_date = "Unknown Date"
            
            # Extract and clean body
            body = get_body_from_email(message)
            
            if body:
                try:
                    # Use email_reply_parser first (handles most cases well)
                    parsed_email = EmailReplyParser.read(body)
                    if parsed_email.fragments:
                        # Find the first non-quoted, non-signature fragment
                        body_content = ""
                        for fragment in parsed_email.fragments:
                            if not fragment.quoted and not fragment.signature and not fragment.hidden:
                                body_content = fragment._content
                                break
                        
                        # If no non-quoted content found, use the first fragment as fallback
                        if not body_content:
                            body_content = parsed_email.fragments[0]._content
                    else:
                        body_content = body
                    
                    
                except Exception as e:
                    logging.warning(f"Failed to parse email reply: {e}")
                    body_content = body
            else:
                body_content = ""
            
            p_body = clean_message(body_content)

            # Skip emails with empty bodies after cleaning (including only whitespace/breaks)
            if is_empty_content(p_body):
                logging.info(f"Skipping email with empty body: '{p_subject}' from {p_sender}")
                skipped_count += 1
                continue

            # Create message object
            msg = make_message(p_sender, p_date, p_subject, p_body)

            # Find or create appropriate chapter
            chapter_name = make_chapter_name(email_date)
            chapter_found = False

            for chapter in chapters:
                if chapter.name == chapter_name:
                    chapter.add_message(msg)
                    chapter_found = True
                    break

            if not chapter_found:
                chapters.append(make_chapter(chapter_name, msg))

            processed_count += 1
            
        except Exception as e:
            logging.error(f"Failed to process message: {e}")
            continue

    logging.info(f"Processed {processed_count} messages into {len(chapters)} chapters")
    if skipped_count > 0:
        logging.info(f"Skipped {skipped_count} emails with empty bodies")

    # Build HTML: compile messages into chapters, then into final book
    chapter_html_parts = []
    
    for chapter in chapters:
        if not chapter.messages:  # Skip empty chapters
            continue
            
        message_html_parts = []
        for message in chapter.messages:
            try:
                msg_html = message_template(
                    message.subject, 
                    message.sender, 
                    message.date, 
                    message.body
                )
                message_html_parts.append(msg_html)
            except Exception as e:
                logging.error(f"Failed to render message template: {e}")
                continue
        
        if message_html_parts:  # Only create chapter if it has messages
            chapter_html = chapter_template(chapter.name, "".join(message_html_parts))
            chapter_html_parts.append(chapter_html)
    
    # Generate final book HTML
    book_html = book_template(title, author, "".join(chapter_html_parts))
    
    # Write output file
    output_file = f"{title}.html"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(book_html)
        logging.info(f"Successfully generated book: {output_file}")
    except Exception as e:
        raise ValueError(f"Failed to write output file '{output_file}': {e}") from e

def print_manual() -> None:
    """Print detailed usage manual when no arguments are provided."""
    manual = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                              MEMEOIRS REDUX                                  ║
║                    Turn your emails into a beautiful book                    ║
╚══════════════════════════════════════════════════════════════════════════════╝

DESCRIPTION:
    Memeoirs Redux converts email correspondence from MBOX files into beautifully 
    formatted HTML books that can be printed as PDFs using Prince XML.

QUICK START:
    1. Export your emails to an MBOX file (see guide below)
    2. Run: python mm-redux.py --title "My Book" --author "Your Name" --mbox emails.mbox
    3. Convert to PDF: prince -s css/6x9_wordy.css "My Book.html" -o "My Book.pdf"

USAGE:
    python mm-redux.py [OPTIONS]

OPTIONS:
    --title TITLE       Book title (default: 'My Book')
    --author AUTHOR     Book author (default: 'John Doe') 
    --mbox MBOX         Path to MBOX file (default: 'sample_mbox')
    --verbose, -v       Enable detailed logging
    --help, -h          Show this help message

GETTING MBOX FILES:
    Gmail: Settings → Forwarding and POP/IMAP → Download data → Mail
    Thunderbird: Tools → Export → Export profile data
    Apple Mail: Mailbox → Export Mailbox
    
    Detailed guide: https://www.jamez.it/blog/2022/06/15/exporting-emails-mbox-file/

AVAILABLE CSS STYLES:
    css/6x9_chatty.css     - 6x9 format, casual styling
    css/6x9_wordy.css      - 6x9 format, text-heavy styling
    css/square_chatty.css  - Square format, casual styling  
    css/square_wordy.css   - Square format, text-heavy styling

PDF GENERATION:
    After generating the HTML file, convert it to PDF using Prince XML:
    
    # Install Prince XML (free for non-commercial use)
    # Download from: https://www.princexml.com/
    
    # Generate PDF with chosen style
    prince -s css/6x9_wordy.css "Your Book.html" -o "Your Book.pdf"

CHAPTER ORGANIZATION:
    Emails are automatically organized into seasonal chapters:
    - Spring '23, Summer '23, Autumn '23, Winter '23-'24
    
OUTPUT:
    Creates an HTML file named after your book title that can be:
    - Opened in any web browser for preview
    - Converted to PDF using Prince XML for printing
    - Sent to print-on-demand services like Lulu.com

For more information, visit: https://github.com/zkg/memeoirs-redux
"""
    print(manual)

def main() -> None:
    """Main entry point for the application."""
    # Check if no arguments provided
    if len(sys.argv) == 1:
        print_manual()
        return
    
    parser = ArgumentParser(
        description="Convert MBOX email files to stylized HTML books",
        epilog="Example: python mm-redux.py --title 'My Correspondence' --author 'John Doe' --mbox emails.mbox"
    )
    parser.add_argument(
        '--title', 
        type=str, 
        default="My Book",
        help="Book title (default: 'My Book')"
    )
    parser.add_argument(
        '--author', 
        type=str, 
        default="John Doe",
        help="Book author (default: 'John Doe')"
    )
    parser.add_argument(
        '--mbox', 
        type=str, 
        default="sample_mbox",
        help="Path to MBOX file (default: 'sample_mbox')"
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate inputs
    if not args.title.strip():
        parser.error("Title cannot be empty")
    if not args.author.strip():
        parser.error("Author cannot be empty")
    
    logging.info(f"Title: {args.title}")
    logging.info(f"Author: {args.author}")
    logging.info(f"MBOX file: {args.mbox}")
    
    try:
        build_book(args.title, args.author, args.mbox)
        logging.info("Book generation completed successfully")
    except (FileNotFoundError, ValueError) as e:
        logging.error(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
