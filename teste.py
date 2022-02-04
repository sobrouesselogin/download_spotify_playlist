#TODO:
#ler do spotify
#tags do beatport
#renomear arquivos para nomes do spotify
#salvar direto na pasta das músicas e criar arquivo com tonalidades
#deixar o arquivo apenas com as queries que falharam
#gravar arquivo de log
#atualizar metadados
import os
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import shutil
import urllib.parse
import traceback
import sys
import warnings
import datetime
import json 

from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
from pprint import pprint

#início do tratamento do parâmetro playlist
playlist_id = ""
for arg in sys.argv:
    if arg.startswith("playlist="):
        playlist_id = arg.split("=",1)[1]
        print("playlist parameter received: using playlist with id: "+playlist_id)

spotify_playlist_queries = []
if playlist_id:
    sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
    pl_id = "spotify:playlist:"+playlist_id
    offset = 0
    while True:
        response = sp.playlist_items(pl_id,
                                     offset=offset,
                                     #fields='items.track.id,items.track.artists[0],items.track.name,total',
                                     fields='items.track.artists.name,items.track.name,total',
                                     additional_types=['track'])
        
        if len(response['items']) == 0:
            break
        
        pprint(response['items'])
        
        for item in response['items']:
            first_artist_name = item.get("track").get("artists")[0].get("name")
            track_name = item.get("track").get("name")
            spotify_playlist_queries.append(first_artist_name+" "+track_name)
        offset = offset + len(response['items'])
        print(offset, "/", response['total'])

    print("query list based on playlist:")
    pprint(spotify_playlist_queries)
#fim do tratamento do parâmetro playlist

#redirecionar print para o arquivo de log
now = datetime.datetime.now()
formatted_datetime = now.strftime('%Y %m %d %H %M %S') + ('-%02d' % (now.microsecond / 10000))
#'2017-09-20T11:52:32-98'
#with open(formatted_datetime+" execution.log", 'w', encoding='utf-8') as f:
#with open("execution.log", 'w', encoding='utf-8') as f:
#with open("execution.log", 'w') as f:
if True:
    #sys.stdout = f

    #ignora warnings
    warnings.filterwarnings("ignore")

    #caminho do driver do navegador
    #necessário ter o navegador chrome instalado na máquina que roda esse script
    #necessário baixar o driver do navegador chrome (utilizar mesma versão do chrome instalado) no site https://chromedriver.chromium.org/downloads
    PATH = "C:\Programas\chromedriver_win32\chromedriver.exe"

    #cria diretório temporário
    working_directory = os.getcwd() 
    temp_path = working_directory + "\\temp\\"
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)
    os.makedirs(temp_path)

    #cria diretório de downloads
    working_directory = os.getcwd() 
    download_path = working_directory + "\\downloaded\\"
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    #seta o diretório de download no navegador
    options = webdriver.ChromeOptions()
    preferences = {"download.default_directory": temp_path, "safebrowsing.enabled":"false"}
    options.add_experimental_option("prefs", preferences)
    options.headless = False

    #opçoes necessárias para que as páginas funcionem de forma esperada no modo headless
    options.add_argument("--window-size=1920,1080")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
    options.add_argument(f'user-agent={user_agent}')

    #inicia navegador
    driver = webdriver.Chrome(PATH, chrome_options=options)        

    #leitura do arquivo com as queries (esse arquivo deve estar formatado como ansi e não utf8)
    if not playlist_id:
        query_file = open('queries.txt', 'r')

    count = 0
    while True:
        count += 1
        #caso tenha sido passado o parâetro playlist, faz as queries baseadas nas tracks dentro dessa playlist, caso contrário, lê o arquivo queries.txt
        if playlist_id:
            if count > len(spotify_playlist_queries)
                break;
            query = spotify_playlist_queries[count-1]
        else:
            query = query_file.readline().strip()

        #sanitiza a query
        mapping = { '&':'%26'}
        for k, v in mapping.items():
            query = query.replace(k, v)

        print("\nquery: "+query);

        #armazena a linha lida no arquivo
        track_query_string = query
        url_encoded_track_query_string = urllib.parse.quote_plus(track_query_string)
        #url_encoded_track_query_string = track_query_string.replace(' ', '+')

        #realiza tentativas de abrir página de download, digitar a query na pesquisa, esperar resultado da pesquisa, clicar no link de download do primeiro resultado
        url = "https://mp3ball.ru?mp3="+query
        
        download_attempt_count = 1
        download_attempt_limit = 3
        download_link_found = False
        while download_attempt_count <= download_attempt_limit and not download_link_found:
            print("download attempt ("+str(download_attempt_count)+") from url: "+url)
            driver.get(url)

            try:
                driver.find_element_by_class_name("link").click()
                download_link_found = True
            except Exception:
                print("download attempt ("+str(download_attempt_count)+") failed")
                download_attempt_count += 1;
                continue
            
            #espera o download ser concluído (existir um arquivo .mp3 no diretório temp)
            download_time_limit = 60
            time_limit_count = 0
            while time_limit_count < download_time_limit:
                if os.listdir(temp_path):
                    downloaded_file_name = os.listdir(temp_path)[0]
                    print("received file: "+downloaded_file_name)
                    if downloaded_file_name.endswith('.mp3'):
                        break
                time_limit_count += 2     
                time.sleep(2)

            if not downloaded_file_name.endswith('.mp3'):
                #significa que não conseguiu baixar no tempo definido em download_time_limit
                print("download attempt ("+str(download_attempt_count)+") failed (download timeout)")
                download_attempt_count += 1;

        if download_attempt_count > download_attempt_limit:
            print("all attempts failed, skipping track")
            continue

        #sanitiza o nome do arquivo
        os.rename(temp_path+downloaded_file_name, temp_path+downloaded_file_name.replace('_(MP3Ball.ru)', ''))
        downloaded_file_name = downloaded_file_name.replace('_(MP3Ball.ru)', '')

        #pega a tonalidade no beatport
        url = "https://www.google.com/search?q=beatport+"
        url += url_encoded_track_query_string
        print("url: "+url)
        driver.get(url)
        driver.find_element_by_xpath('(//h3)[1]/../../a').click()

        #na página do beatport, verifica a tonalidade
        try:
            beatport_key = driver.find_element_by_class_name('interior-track-key').find_element_by_class_name('value').text
        except Exception:
            beatport_key = "key not found"
        
        print("beatport key: "+beatport_key)

        #cria diretório da tonalidade
        key_path = download_path+beatport_key+"\\"
        if not os.path.exists(key_path):
            os.makedirs(key_path)

        #joga para a pasta downloaded / tonalidade descoberta
        shutil.move(temp_path+downloaded_file_name, key_path+downloaded_file_name)

        #fim da iteração de leitura de linha do arquivo
    query_file.close()
    print("end of script");






