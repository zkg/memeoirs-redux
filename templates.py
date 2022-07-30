# -*- coding: utf-8 -*-
def book_template(title, author, chapters):
    return """
<!DOCTYPE html>
<html><head>
<meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <meta charset="UTF-8">
    <title> %(title)s</title>
    <script>
    function getText(e) {
      var text = "";
      for (var x = e.firstChild; x != null; x = x.nextSibling) {
        if (x.nodeType == x.TEXT_NODE) {
          text += x.data;
        } else if (x.nodeType == x.ELEMENT_NODE) {
          text += getText(x);
        }
      }
      return text;
    }

    function maketoc() {
      var hs = document.getElementsByClassName("chapter");
      var toc = document.getElementById('toc');
      for(var i = 0; i < hs.length; i++) {
        var h = hs[i].getElementsByTagName("h1")[0];
        var text = document.createTextNode(getText(h));
        var span = document.createElement("span");
        span.appendChild(text);
        h.setAttribute("id", "ch"+i);
        var link = document.createElement("a");
        link.setAttribute("href", "#ch"+i);
        link.appendChild(span);
        toc.appendChild(link);
      }
    }
    </script>
  </head>
  <body onload="maketoc();">
    <!-- PAGE: facsimile -->
    <div class="facsimile">
              <h2>Memeoirs</h2>
        <h1> %(title)s</h1>
        <h3> %(author)s</h3>
    </div>
    <!-- ENDPAGE: facsimile -->

    <!-- PAGE: colophon -->
    <div class="colophon">
      <p id="copyright">
        %(title)s © %(author)s
      </p>

              <p>Memeoirs does not review or control this book, is not 
responsible for its contents, and does not represent that the content is
 appropriate.</p>
        <p>The exchanges featured in this book were compiled on www.memeoirs.com<br>
        Visit the website for more digital to print goodness.</p>
          </div>
    <!-- ENDPAGE: colophon -->

        %(chapters)s

    <!-- LAST PAGE: even page with final memeoirs signature -->
    <div class="final"><p class="signature">Visit us at www.memeoirs.com</p></div>
    <!-- END LAST PAGE -->
  

</body></html>
    """ % {'title':title, 'author':author, 'chapters': chapters}

def chapter_template(name, messages):
    return """
    <div class="chapter">
    <h1 id="ch0">%(name)s</h1>
        %(messages)s
    </div>
    """ % {'name':name, 'messages':messages}


def message_template(subject, fromm, date, body):
    return """
    <div class="email">
      <div class="titles">
        <h2 class="title">
                 %(subject)s
        </h2>
        <h3 class="date">
            %(date)s
        </h3>
        <h4 class="author">
            %(fromm)s
        </h4>
      </div>
      <div class="message">
        %(body)s
      </div>
    </div>
    """ % {'subject':subject, 'fromm':fromm, 'date':date, 'body': body}
