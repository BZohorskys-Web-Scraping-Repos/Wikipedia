import aiohttp
import asyncio
import curses
import itertools
import logging
import os
import sys
import textwrap
import urllib
import webbrowser

from lxml import etree

SITE = 'https://en.wikipedia.org/wiki/'
CURRENT_EVENTS = 'https://en.wikipedia.org/wiki/Portal:Current_events'
TAB = '  '
TERMINAL_WIDTH = os.get_terminal_size().columns

logging.basicConfig(
    level=logging.WARN,
    format='%(asctime)-15s [%(levelname)s] %(funcName)s: %(message)s',
)

async def get_webpage(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            code = response.status
            html = await response.text()
            return {'code':code, 'html':html}

async def idleAnimation(task):
    for frame in itertools.cycle(r'-\|/-\|/'):
        if task.done():
            print('\r', '', sep='', end='', flush=True)
            break;
        print('\r', '', sep='', end='', flush=True)
        await asyncio.sleep(0.2)

def interactive_console(screen, data):
    header = "(#/totalPages)\n"
    footer = "\n\nPage Down, Page Up, Open Wiki site, or Quit? (j,k,o,q)"
    max_y, max_x = screen.getmaxyx()
    data['pages'] = setPages(max_x, max_y - 1, header, footer, data['text'])
    pageNumber = 0
    while pageNumber < len(data['pages']):
        screen.clear()
        screen.addstr(data['pages'][pageNumber])
        validResponse = False
        while not validResponse:
            user_response = screen.getkey()
            if user_response == 'j':
                validResponse = True
                pageNumber += 1
            elif user_response == 'k':
                if pageNumber != 0:
                    validResponse = True
                    pageNumber -= 1
            elif user_response == 'o':
                validResponse = True
                webbrowser.open(data['url'])
            elif user_response == 'q':
                validResponse = True
                pageNumber = len(data['pages'])

def setPages(max_x, max_y, header, footer, text):
    headerFooter = header + footer
    idx = 0
    max_y_modifier = 0
    while idx < len(headerFooter):
        i = 0
        while i < max_y and idx < len(headerFooter):
            j = 0
            while j < max_x and idx < len(headerFooter):
                if headerFooter[idx] == '\n':
                    j = max_x - 1
                j += 1
                idx += 1
            i += 1
            max_y_modifier += 1

    pages = []
    modified_max_y = max_y - max_y_modifier
    if modified_max_y < 1:
        errorResponse = "Sorry, your window is too small to display the output correctly. Increase it if possible. Quit (q)."
        pages.append(errorResponse)
        return pages

    idx = 0
    while idx < len(text):
        page = [header]
        i = 0
        while i < modified_max_y and idx < len(text):
            j = 0
            while j < max_x and idx < len(text):
                if text[idx] == '\n':
                    j = max_x - 1
                page.append(text[idx])
                j += 1
                idx += 1
            i += 1
        page.append(footer)
        pages.append(''.join(page))

    for idx, page in enumerate(pages):
        pageNumber = str(idx + 1)
        newHeader = "(" + pageNumber + "/" + str(len(pages)) + ")\n"
        pages[idx] = page.replace(header, newHeader)

    return pages

def is_paragraph_empty(paragraph):
    logging.info(locals())
    return True if paragraph.strip() == '' else False

async def get_wiki_search(query_string):
    logging.info(locals())
    search_url = ''.join([SITE, query_string])
    webRequestTask = asyncio.create_task(get_webpage(search_url))
    await idleAnimation(webRequestTask)
    if webRequestTask.result()['code'] == 200:
        topicData = {
            'pages': [],
            'text': '',
            'url': ''
        }
        page_html = etree.HTML(webRequestTask.result()['html'])
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
        topicData['url'] = 'https://' + urllib.parse.quote(search_url.replace('https://', ''))
        topicData['text'] = ''.join(paragraph_text_list)
        curses.wrapper(interactive_console, topicData)

    else:
        print(f'Recieved {webRequestTask.result()["code"]} response code.')

async def get_wiki_current_events():
    logging.info(locals())
    webRequestTask = asyncio.create_task(get_webpage(CURRENT_EVENTS))
    await idleAnimation(webRequestTask)
    if webRequestTask.result()['code'] == 200:
        data = {
            'pages': [],
            'text': [],
            'url': CURRENT_EVENTS
        }
        page_html = etree.HTML(webRequestTask.result()['html'])
        quick_facts = page_html.xpath('//div[@role="region"]/ul/li')
        on_going = page_html.xpath('//div[@role="region"]//div[contains(@class,"hlist")]')[0]

        data['text'].append('Topics in the News:\n')
        for idx, fact in enumerate(quick_facts):
            text = ''.join(fact.xpath('./descendant-or-self::*/text()'))
            data['text'].append(''.join(textwrap.wrap(text,TERMINAL_WIDTH,initial_indent=TAB + ' * ', subsequent_indent='\n' + TAB + ' ')) + '\n')
        on_going_data = ''.join(on_going.xpath("./descendant-or-self::*/text()"))
        on_going_data = on_going_data.replace('\n','\n' + TAB)
        data['text'].append('Ongoing: ' + on_going_data + '\n')
        currentEvents = page_html.xpath('//div[@class="current-events"]')
        for day in currentEvents:
            date = day.xpath('.//span[@class="summary"]/text()')
            date = date[0] + date[1] + '\n'
            paragraphs = day.xpath('.//div[@class="current-events-content description"]/p')
            topics = day.xpath('.//div[@class="current-events-content description"]/ul')
            if paragraphs:
                data['text'].append(date)
                for idx in range(len(paragraphs)):
                    data['text'].append(TAB + ''.join(paragraphs[idx].xpath('./descendant-or-self::*/text()')))
                    get_nested_items(topics[idx], 1, data['text'])
        data['text'] = ''.join(data['text'])
        curses.wrapper(interactive_console, data)
    else:
        print(f'Recieved {webRequestTask.result()["code"]} response code.')


def get_nested_items(topic, indent, textList):
    logging.info(locals())
    tree = topic.xpath('./li')
    for branch in tree:
        get_nested_items_helper(branch, indent + 1, textList)

def get_nested_items_helper(branch, indent, textList):
    logging.info(locals())
    if(branch.xpath('./ul')):
        textList.append((TAB * indent) + ''.join(branch.xpath('./a/text()')) + '\n')
        topics = branch.xpath('./ul')
        for topic in topics:
            get_nested_items(topic, indent, textList)
    else:
        textList.append(''.join(textwrap.wrap(''.join(branch.xpath('./descendant-or-self::*/text()')), TERMINAL_WIDTH, initial_indent=TAB * (indent + 1), subsequent_indent="\n" + TAB * indent)) + '\n')