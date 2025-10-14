#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML templates for generating email books."""

def book_template(title: str, author: str, chapters: str) -> str:
    """Generate the complete HTML book template.
    
    Args:
        title: Book title
        author: Book author
        chapters: HTML content for all chapters
        
    Returns:
        Complete HTML book as string
    """
    return f"""
<!DOCTYPE html>
<html><head>
<meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <meta charset="UTF-8">
    <title>{title}</title>
    <script>
    function getText(e) {{
      var text = "";
      for (var x = e.firstChild; x != null; x = x.nextSibling) {{
        if (x.nodeType == x.TEXT_NODE) {{
          text += x.data;
        }} else if (x.nodeType == x.ELEMENT_NODE) {{
          text += getText(x);
        }}
      }}
      return text;
    }}

    function maketoc() {{
      var hs = document.getElementsByClassName("chapter");
      var toc = document.getElementById('toc');
      for(var i = 0; i < hs.length; i++) {{
        var h = hs[i].getElementsByTagName("h1")[0];
        var text = document.createTextNode(getText(h));
        var span = document.createElement("span");
        span.appendChild(text);
        h.setAttribute("id", "ch"+i);
        var link = document.createElement("a");
        link.setAttribute("href", "#ch"+i);
        link.appendChild(span);
        toc.appendChild(link);
      }}
    }}
    </script>
  </head>
  <body onload="maketoc();">
    <!-- PAGE: facsimile -->
    <div class="facsimile">
              <h2>Memeoirs</h2>
        <h1>{title}</h1>
        <h3>{author}</h3>
    </div>
    <!-- ENDPAGE: facsimile -->

    <!-- PAGE: colophon -->
    <div class="colophon">
      <p id="copyright">
        {title} © {author}
      </p>

              <p>Memeoirs does not review or control this book, is not 
responsible for its contents, and does not represent that the content is
 appropriate.</p>
        <p>The exchanges featured in this book were compiled on www.memeoirs.com<br>
        Visit the website for more digital to print goodness.</p>
          </div>
    <!-- ENDPAGE: colophon -->

        {chapters}

    <!-- LAST PAGE: even page with final memeoirs signature -->
    <div class="final"><p class="signature">Visit us at www.memeoirs.com</p></div>
    <!-- END LAST PAGE -->
  

</body></html>
    """

def chapter_template(name: str, messages: str) -> str:
    """Generate HTML template for a chapter.
    
    Args:
        name: Chapter name
        messages: HTML content for all messages in the chapter
        
    Returns:
        Chapter HTML as string
    """
    return f"""
    <div class="chapter">
    <h1 id="ch0">{name}</h1>
        {messages}
    </div>
    """


def message_template(subject: str, sender: str, date: str, body: str) -> str:
    """Generate HTML template for an individual message.
    
    Args:
        subject: Email subject line
        sender: Email sender name
        date: Formatted date string
        body: Processed email body content
        
    Returns:
        Message HTML as string
    """
    return f"""
    <div class="email">
      <div class="titles">
        <h2 class="title">
                 {subject}
        </h2>
        <h3 class="date">
            {date}
        </h3>
        <h4 class="author">
            {sender}
        </h4>
      </div>
      <div class="message">
        {body}
      </div>
    </div>
    """
