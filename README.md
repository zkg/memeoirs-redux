# Memeoirs Redux

Turn your emails into a book.

## Description

Memeoirs was a service that helped people create a book out of their email correspondence. There were a few use cases, but the most common ones was collecting and gifting a memento for a friend or a lover. The service is no more, but the core of Memeoirs was actually simple enough to be provided in a short Python script, provided you are willing to do some leg-work, particularly in the phase of downloading and saving the actual emails you need. Once you have an MBOX file with your messages, you are ready to execute the script that will generate an html version of your book. Using a tool called Prince on the html file and one of the styles provided, you will finally get a PDF that you can send to Lulu or similar services to create a physical book.

## Getting Started

### Dependencies

* [Prince](https://www.princexml.com/) - Provided that your project is for non-commercial use, you should be able to use Prince for free. Download and install it.
* Fonts - The css used for styling a book use the following fonts: AGaramond LT, AGaramond RegularSC, AGaramond LT Bold, HelveticaNeueLT Com 45 Lt, HelveticaNeueLT Std Blk, HelveticaNeueLT Com 35 Th. Buy them, they are worth it. Or replace them with your own creative vision.

### Installing

* Download the files
* pip install -r requirements.txt

### Executing program

* How to run the program

```
python mm-redux.py --title "my_book" --author "John Doe" --mbox my_correspondence.mbox
```


* Once your .html file is generated, use it to create a PDF with Prince, passing as parameters one of the styles included in the css folder. 6x9_chatty.css and 6x9_wordy.css should be good for most cases.

```
prince -s css/6x9_wordy.css my_book.html -o my_book.pdf
```

## Help

* Creating the mbox file could end up being the largest portion of this project. Here's a short guide on how to do that using Gmail and Thunderbird.

* Filtering of reply messages is not perfect. There are hundreds of different clients reply-quoting messages in different way. If the standard filter does not work, you may want to add your own routine to the clean_message function.

*Last touches: feel free to make any final edit to the html file before generating the PDF. 


## Authors

Memeoirs was a product of love, and many people helped in making it shine. Some of the ideas in this script where originally implemented as a web-app by Paulo Pino, Fred Rocha, Carlos Pires and Pedro Rio. Layout and design of the books was provided by Paulo Patricio.

## Version History

* 0.1
    * Initial Release


