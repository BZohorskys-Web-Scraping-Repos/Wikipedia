import requests
import sys
import webbrowser
import logging
import textwrap
import os
import urllib

from lxml import etree
from lxml import html

SITE = 'https://en.wikipedia.org/wiki/'
CURRENT_EVENTS = 'https://en.wikipedia.org/wiki/Portal:Current_events'
TAB = '  '
TERMINAL_WIDTH = os.get_terminal_size().columns

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)-15s [%(levelname)s] %(funcName)s: %(message)s',
)

def is_paragraph_empty(paragraph):
    return True if paragraph.strip() == '' else False

def get_wiki_search(query_string):
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
        paragraph_text_list = []
        for paragraph in paragraphs:
            styles = paragraph.xpath('./descendant::style')
            for junk_data in styles:
                junk_data.getparent().remove(junk_data)
            paragraph_text = ''.join(paragraph.xpath('./descendant-or-self::*/text()'))
            if not is_paragraph_empty(paragraph_text):
                paragraph_text_list.append(TAB*2)
                paragraph_text_list.extend(paragraph_text.strip())
                paragraph_text_list.append('\n\n')

        paragraph_text_list.pop()
        paragraph_text_list.extend(['\n\n', 'https://' + urllib.parse.quote(search_url.replace('https://', ''))])
        final = "".join(paragraph_text_list)
        os.system(f'echo "{final}" | vim - -R')

    else:
        print(f'Recieved {r.status_code} response code.')

def get_wiki_current_events():   
    r = requests.get(CURRENT_EVENTS)
    if r.status_code == 200:
        page_html = etree.HTML(r.content)
        quick_facts = page_html.xpath('//div[@role="region"]/ul/li')
        on_going = page_html.xpath('//div[@role="region"]//div[contains(@class,"hlist")]')[0]
        
        print('Topics in the News:')
        for idx, fact in enumerate(quick_facts):
            text = ''.join(fact.xpath('./descendant-or-self::*/text()'))
            print("\n".join(textwrap.wrap(text,TERMINAL_WIDTH,initial_indent=TAB*2, subsequent_indent=TAB)))
            print()
        on_going_data = ''.join(on_going.xpath("./descendant-or-self::*/text()"))
        on_going_data = on_going_data.replace('\n','\n' + TAB)
        print(f'Ongoing: {on_going_data}')
        print()

        date = page_html.xpath('//span[@class="summary"]/text()')
        date = date[0] + date[1]
        
        event = page_html.xpath('//div[@class="vevent"]')[0]
        description = event.xpath('.//div[@class="description"]')[0]
        paragraphs = description.xpath('./p')
        topics = description.xpath('./ul')
        if not paragraphs:
            return
        print(f'{date}:')
        for idx in range(len(paragraphs)):
            print(f"{TAB}{''.join(paragraphs[idx].xpath('./descendant-or-self::*/text()'))}", end='')
            get_nested_items(topics[idx], 1)

    user_response = input('Open wikipedia page or quit? (o/q): ')
    if user_response == 'o':
        webbrowser.open(CURRENT_EVENTS)

def get_nested_items(topic, indent):
    tree = topic.xpath('./li')
    for branch in tree:
        get_nested_items_helper(branch, indent + 1)

def get_nested_items_helper(branch, indent):
    if(branch.xpath('./ul')):
        print(f"{TAB * indent}{''.join(branch.xpath('./a/text()'))}")
        topics = branch.xpath('./ul')
        for topic in topics:
            get_nested_items(topic, indent)
    else:
        print('\n'.join(textwrap.wrap(''.join(branch.xpath( './descendant-or-self::*/text()')), TERMINAL_WIDTH, initial_indent=TAB * (indent + 1), subsequent_indent=TAB * indent)))
        input()

def main():
    if len(sys.argv) != 2:
        if len(sys.argv) < 2:
            print('Error: Not enough arguments provided. Please provide a search term.')
            return
        else:
            print('Error: Too many arguments provided.')
            return
    
    query_string = sys.argv[1]
    if query_string == '--news':
        get_wiki_current_events()
    else:
        get_wiki_search(query_string)

if __name__ == '__main__':
    main()
