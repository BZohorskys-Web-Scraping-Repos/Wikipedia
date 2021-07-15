import requests
import sys
import webbrowser
import logging
from lxml import etree

SITE = 'https://en.wikipedia.org/wiki/'

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)-15s [%(levelname)s] %(funcName)s: %(message)s',
)

def main():
    if len(sys.argv) != 2:
        if len(sys.argv) < 2:
            print('Error: Not enough arguments provided. Please provide a search term.')
            return
        else:
            print('Error: Too many arguments provided.')
            return

    query_string = sys.argv[1]
    search_url = ''.join([SITE, query_string])
    r = requests.get(search_url)
    if r.status_code == 200:
        page_html = etree.HTML(r.content)
        vcards = page_html.xpath('//table[contains(@class, "vcard")]')
        for card in vcards:
            card.getparent().remove(card)
        infoboxes = page_html.xpath('//table[contains(@class, "infobox")]')
        for infobox in infoboxes:
            infobox.getparent().remove(infobox)
        paragraphs = page_html.xpath('//div[@id="toc"]/preceding::p')
        for paragraph in paragraphs:
            styles = paragraph.xpath('./descendant::style')
            for junk_data in styles:
                junk_data.getparent().remove(junk_data)
            paragraph_text = ''.join(paragraph.xpath('./descendant-or-self::*/text()'))
            if not is_paragraph_empty(paragraph_text):
                print(f'{"".join(paragraph_text.rstrip())}\n')

        user_response = input('Open wikipedia page or quit? (o/q): ')
        if user_response == 'o':
            webbrowser.open(search_url)
    else:
        print(f'Recieved {r.status_code} response code.')

def is_paragraph_empty(paragraph):
    return True if paragraph.strip() == '' else False


if __name__ == '__main__':
    main()
