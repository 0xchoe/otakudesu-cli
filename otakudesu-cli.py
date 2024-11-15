import base64
import json
from urllib.parse import urlparse
from os import system
import sys
import re

import requests
from bs4 import BeautifulSoup
import inquirer

base_url = "https://otakudesu.cloud"

class Otakudesu:
    def __init__(self, base_url,):
        self.base_url = base_url
        self.re_pattern = ' Subtitle Indonesia'


    def anime_search(self, query):
        response = requests.get(f'{self.base_url}/?s={query}&post_type=anime')
        soup = BeautifulSoup(response.content, 'html.parser')

        data = {}
        anime_list = soup.select('ul.chivsrc li')

        for anime in anime_list:
            title_and_link = anime.find('a')
            title_re = re.sub(self.re_pattern, '', title_and_link.text)
            data[title_re] = title_and_link['href']

        return data

    def episode_list(self, anime_link):
        response = requests.get(anime_link)
        soup = BeautifulSoup(response.content, 'html.parser')

        data = {}
        episodes = soup.select('div.episodelist ul li')

        for episode in episodes:
            title_and_link = episode.find('a')
            title_re = re.sub(self.re_pattern, '', title_and_link.text)
            data[title_re] = title_and_link['href']

        return data

    def get_mirror(self, episode_link):
        response = requests.get(episode_link)
        soup = BeautifulSoup(response.content, 'html.parser')

        data = {}
        anime_list = soup.select('ul.m720p li')

        for anime in anime_list:
            title_and_data = anime.find('a')
            decoded_data = base64.b64decode(title_and_data['data-content']).decode('utf-8')
            data[title_and_data.text] = decoded_data

        if not data:
            print('Episode yang dipilih invalid')
            exit()
            
        return data

    def get_mirror_link(self, mirror_data):
        url = f'{self.base_url}/wp-admin/admin-ajax.php'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        nonce = requests.post(url,  {
        'action': 'aa1208d27f29ca340c92c66d1926f13f' # constant
        }, headers=headers)
        nonce = json.loads(nonce.text)
        nonce = nonce['data']

        post_data = json.loads(mirror_data)
        post_data['nonce'] = nonce
        post_data['action'] = '2a3505c93b0035d3f455df82bf976b84' # constant

        post_response = requests.post(url, post_data, headers=headers)
        post_response = json.loads(post_response.text)

        decoded_post_response = base64.b64decode(post_response['data']).decode('utf-8')

        soup = BeautifulSoup(decoded_post_response, 'html.parser')

        link = soup.find('iframe')
        
        if link == None:
            print('Mirror tidak dapat digunakan')
            exit()

        link = link['src']
        
        # pixeldrain & yourupload
        pdrain_url = 'https://www.pixeldrain.com'
        your_url = 'https://desudrive.com/dstream/yourupload'

        if pdrain_url in link:
            parsed_link = urlparse(link)
            path = parsed_link.path.split('/')
            url_id = path[2]
            link = f'{pdrain_url}/api/file/{url_id}'

        elif your_url in link:
            parsed_link = urlparse(link)
            path = parsed_link.query
            path_split = path.split('=')
            link = f'https://www.yourupload.com/embed/{path_split[1]}'

        return link


def launch_browser(url):
    if hasattr(sys, 'getandroidapilevel'):
        print(f'> Executing: termux-open-url {url}')
        system(f'termux-open-url {url}')

    elif sys.platform == 'win32':
        print(f'> Executing: start {url}')
        system(f'start {url}')

    else:
        print(f'> Executing: xdg-open {url}')
        system(f'xdg-open {url}')


def clear_screen():
    if sys.platform == 'win32':
        system('cls')
        
    else:
        system('clear')


anime = Otakudesu(base_url)

# main
def main():
    try:
        find_anime = inquirer.text(message='Cari Anime')
        anime_list = anime.anime_search(find_anime)

        if not anime_list:
            print(f'Anime tidak ditemukan')
            exit()

        clear_screen()

        anime_choice = inquirer.list_input('Pilih Anime', choices=list(anime_list))
        anime_link = anime_list[anime_choice]
        clear_screen()
        print(f'> Anime: {anime_choice}')
        
        get_episode = anime.episode_list(anime_link)
        episode_choice = inquirer.list_input('Pilih Episode', choices=list(get_episode))
        episode_link = get_episode[episode_choice]
        clear_screen()
        print(f'> Episode: {episode_choice}')

        mirror_list = anime.get_mirror(episode_link)
        mirror_choice = inquirer.list_input('Pilih Mirror', choices=list(mirror_list))
        mirror_data = mirror_list[mirror_choice]
        clear_screen()
        
        mirror_link = anime.get_mirror_link(mirror_data)

        print(f'> Anime: {anime_choice}\n> Episode: {episode_choice}\n> Mirror: {mirror_choice}\n> Mirror link: {mirror_link}')
        launch_browser(mirror_link)

    except KeyboardInterrupt:
        print('Operasi dibatalkan oleh user')

    except requests.exceptions.ConnectionError:
        print('Connection error')


if __name__ == '__main__':
    main()