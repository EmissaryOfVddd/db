import requests
import bs4
import logging
from db import TABLE_NAME, cursor, connection

session = requests.sessions.Session()
domain = 'https://habr.com/'
tags = {
    'блокировка': 'base',
    'роскомнадзор': 'base',

    'DPI': 'combinable',
    'VPN': 'combinable',
    'обход': 'combinable',
    
    'youtube': 'specifics',
    'discord': 'specifics',
    'steam': 'specifics',
    'twitch': 'specifics',
}
request_string = 'ru/search/?q=блокировка&target_type=posts&order=date'
logger = logging.getLogger(' SCRAPER_LOG ')
logging.basicConfig(filename='log.txt', level=logging.INFO, encoding='UTF-8')

class ScrapRes:
    title: str
    text: str
    href: str

    def __init__(self, title: str, text: str, href: str):
        self.title = title
        self.text = text
        self.href = href


class ScrapReq:
    domain: str
    tags: dict[str | str]
    session: requests.sessions.Session
    queue: list[tuple[str, str]] = []

    def __init__(self, domain: str, session: requests.sessions.Session, tags: dict[str | str]):
        self.domain = domain
        self.tags = tags
        self.session = session

    def req_to_page(self, req_body: str) -> str:
        request_str = f'{self.domain}{req_body}'
        logger.info(f'REQUEST TO: {request_str}')
        response = self.session.get(request_str)
        logger.info(f'REQUEST STATUS CODE: {response.status_code}')
        if response.status_code != 200:
            logger.error('FUCK')
            logger.info(f'REQUEST FAILED WITH: {response.reason}')
            return None
        
        return response.text
            
    def push(self, url: tuple[str, str]):
        self.queue.append(url)

    def pop(self) -> tuple[str, str]:
        return self.queue.pop(0)

    def get_entry(self) -> ScrapRes | None:
        (title, href) = self.pop()
        resp = self.req_to_page(href)
        if resp is None:
            return None
        page_s = bs4.BeautifulSoup(resp, 'html.parser')
        main_body = page_s.find('div', 'tm-misprint-area')
        text = ''
        for p in main_body.find_all('p'):
            text += f'{p.text}\n'

        return ScrapRes(title, text, f'{self.domain}{href}')
        

    def search_page(self, req_body: str) -> str | None:
        resp = self.req_to_page(req_body)
        
        soup = bs4.BeautifulSoup(resp, 'html.parser')
        article_items = soup.find_all('article', class_='tm-articles-list__item')
        pagination = soup.find('a', attrs={ 'data-pagination-next': True })

        if pagination != None:
            req_body = pagination.get('href')
        else:
            req_body = ''

        for item in article_items:
            a = item.find('a', class_='tm-title__link')
            page_url = a.get('href')
            title = a.find('span').text
            self.push((title, page_url))
            
        return req_body

if __name__ == '__main__':
    habr = ScrapReq(domain, session, tags)
    next = request_string
    while next != None and next != '':
        next = habr.search_page(next)

    entries = []
    while len(habr.queue) != 0:
        entry = habr.get_entry()
        if entry is None:
            continue
        cursor.execute(f'SELECT * from {TABLE_NAME} where href = %s', (entry.href, ))
        res = cursor.fetchall()
        if len(res) != 0:
            continue
        sql = f'INSERT INTO {TABLE_NAME} (href, title, text) VALUES (%s, %s, %s)'
        val = (entry.href, entry.title, entry.text)
        cursor.execute(sql, val)
        
    connection.commit()

