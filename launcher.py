import asyncio
import src.wiki
import sys

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
        asyncio.run(src.wiki.get_wiki_current_events())
    else:
        asyncio.run(src.wiki.get_wiki_search(query_string))

if __name__ == '__main__':
    sys.exit(main())