#TODO:
#pegar bpm do beatport tb
#logar progresso (track tal de tal, mostrar o tempo que demorou)
#acelerar consulta no tunebat (fazer webdriver checar antes da pagina ficar 100% carregada)
#separar em módulos (download de site específico, apenas setar as keys)
#implementar opcao de apenas setar as tonalidades
#levantar dependencias: selenium, driver, mutagen, spotipy
#informar tracks que falharam o download
#informar tracks que falharam tonalidade
#deixar o arquivo apenas com as queries que falharam
#validar se diretorio de download existe (ok)
#puxar dados do tunebeat quando não encontrar no beatport: https://tunebat.com/Info/Gimme-More-Dominique-Lamee/0YAmUSpoikne38Krw5U5dN (OK)
#validar arquivos pequenos (tentar novamente) (OK)
#receber pasta de download como parâmetro (OK)
#esperar tecla antes de fechar o script (OK)
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
from id3_tag_utils import set_file_tkey_tag
from beatport_selenium_wrapper import get_beatport_key
from tunebat_selenium_wrapper import get_tunebat_key

#redirecionar print para o arquivo de log
#now = datetime.datetime.now()
#formatted_datetime = now.strftime('%Y %m %d %H %M %S') + ('-%02d' % (now.microsecond / 10000))
#with open(formatted_datetime+" execution.log", 'w', encoding='utf-8') as f:
#with open("execution.log", 'w', encoding='utf-8') as f:
#with open("execution.log", 'w') as f:
if True:#stdout

    #ignora warnings
    warnings.filterwarnings("ignore")

    #parâmetros de configuração
    #caminho do driver do navegador
    #necessário ter o navegador chrome instalado na máquina que roda esse script
    #necessário baixar o driver do navegador chrome (utilizar mesma versão do chrome instalado) no site https://chromedriver.chromium.org/downloads
    config_selenium_chrome_driver = "C:\Programas\chromedriver_win32\chromedriver.exe"
    
    parameter_playlist_id = ""
    skip_download = False
    key_list_file = ""
    parameter_download_location = ""
    parameter_playlist_start_from = ""
    parameter_skip_existing_files = False
    for arg in sys.argv:
        #tratamento do parâmetro do local de download
        if arg.startswith("--download_location="):
            parameter_download_location = arg.split("=",1)[1]
            parameter_download_location = parameter_download_location.strip('"')
            if not (parameter_download_location.endswith("/") or parameter_download_location.endswith("\\")):
                parameter_download_location += "/"
            print("download_location parameter received:")
            #verifica se a pasta especificada existe
            if not os.path.isdir(parameter_download_location):
                print("error: download_location is not accessible")
                sys.exit()
            
            print("saving files at: "+parameter_download_location)

        #início do tratamento do parâmetro skip_existing_files
        if arg.startswith("--skip_existing_files"):
            print("skip_existing_files parameter received")
            print("ignoring existing files")
            parameter_skip_existing_files = True
        
        #início do tratamento do parâmetro playlist
        if arg.startswith("--playlist="):
            parameter_playlist_id = arg.split("=",1)[1]
            print("playlist parameter received: using playlist with id: "+parameter_playlist_id)

        #início do tratamento do parâmetro playlist -> playlist_start_from
        if arg.startswith("--playlist_start_from="):
            parameter_playlist_start_from = arg.split("=",1)[1]
            print("playlist_start_from parameter received:")
            print("starting from track : "+parameter_playlist_start_from)

        #início do tratamento do parâmetro show_browser
        parameter_show_browser = False
        if arg.startswith("--show_browser"):
            parameter_show_browser = True

        #início do tratamento do parâmetro --skip_download
        if arg.startswith("--skip_download"):
            skip_download = True
            print("skipping downloads parameter received")

        #início do tratamento do parâmetro --generate_key_list_file
        if arg.startswith("--generate_key_list_file="):
            key_list_file = arg.split("=",1)[1]
            print("generating key list file: "+key_list_file)

    if not parameter_download_location:
        working_directory = os.getcwd() 
        parameter_download_location = working_directory + "\\downloads\\"
        if not os.path.exists(parameter_download_location):
            os.makedirs(parameter_download_location)
        print("download_location parameter not specified: saving files at: "+parameter_download_location)

    spotify_playlist_queries = []
    spotify_playlist_track_names = []
    spotify_playlist_failed_track_names = []
    if parameter_playlist_id:
        sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
        pl_id = "spotify:playlist:"+parameter_playlist_id
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
                spotify_playlist_track_names.append(
                    (first_artist_name+" - "+track_name)
                    .replace("*", " ")
                    .replace("/", " ")
                )
            offset = offset + len(response['items'])
            print(offset, "/", response['total'])

        print("query list based on playlist:")
        pprint(spotify_playlist_queries)
    #fim do tratamento do parâmetro playlist
    
    #sys.stdout = f

    #cria diretório temporário de download
    working_directory = os.getcwd() 
    temp_path = working_directory + "\\temp\\"
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)
    os.makedirs(temp_path)

    #cria diretório de downloads
##    working_directory = os.getcwd() 
##    download_path = working_directory + "\\downloaded\\"
##    if not os.path.(download_path):
##        os.makedirs(download_path)

    #seta o diretório de download no navegador
    options = webdriver.ChromeOptions()
    preferences = {"download.default_directory": temp_path, "safebrowsing.enabled":"false"}
    options.add_experimental_option("prefs", preferences)
    options.headless = True
    if parameter_show_browser:
        options.headless = False

    #opçoes necessárias para que as páginas funcionem de forma esperada no modo headless
    options.add_argument("--window-size=1920,1080")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--log-level=3') # INFO = 0, WARNING = 1, LOG_ERROR = 2, LOG_FATAL = 3.
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
    options.add_argument(f'user-agent={user_agent}')

    #inicia navegador
    driver = webdriver.Chrome(config_selenium_chrome_driver, chrome_options=options)

   #leitura do arquivo com as queries (esse arquivo deve estar formatado como ansi e não utf8)
    if not parameter_playlist_id:
        query_file = open('queries.txt', 'r')

    count = 0
    if parameter_playlist_start_from:
        count = int(parameter_playlist_start_from) - 1
    while True:
        count += 1
        
        #caso tenha sido passado o parâmetro playlist, faz as queries baseadas nas tracks dentro dessa playlist, caso contrário, lê o arquivo queries.txt
        if parameter_playlist_id:
            if count > len(spotify_playlist_queries):
                break;
            query = spotify_playlist_queries[count-1]
        else:
            query = query_file.readline().strip()

        print("\ndownloading track " + str(count) + "/"+ str(len(spotify_playlist_track_names)))

        #sanitiza a query
        mapping = { '&':'%26'}
        for k, v in mapping.items():
            query = query.replace(k, v)

        print("query: "+query);
        if parameter_skip_existing_files:
            path_of_file_to_be_created = parameter_download_location+spotify_playlist_track_names[count-1]+".mp3"
            if os.path.isfile(path_of_file_to_be_created): 
                print("file exists, skipping")
                continue

        #armazena a linha lida no arquivo
        track_query_string = query
        url_encoded_track_query_string = urllib.parse.quote_plus(track_query_string)
        #url_encoded_track_query_string = track_query_string.replace(' ', '+')

        #realiza tentativas de abrir página de download, digitar a query na pesquisa, esperar resultado da pesquisa, clicar no link de download do primeiro resultado
        url = "https://mp3ball.ru?mp3="+query
        
        download_attempt_count = 1
        download_attempt_limit = 3
        download_success = False
        if not skip_download:
            while download_attempt_count <= download_attempt_limit and not download_success:
                print("download attempt ("+str(download_attempt_count)+") from url: "+url)
                driver.get(url)

                try:
                    driver.find_element_by_class_name("link").click()
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
                        if downloaded_file_name.endswith('.mp3'):
                            #checa o tamanho do arquivo para ver se não veio lixo
                            file_size = os.path.getsize(temp_path+downloaded_file_name)
                            print("received file: " + downloaded_file_name + ". file size: "+str(file_size) + " bytes")
                            break
                    time_limit_count += 2     
                    time.sleep(2)

                if not downloaded_file_name.endswith('.mp3'):
                    #significa que não conseguiu baixar no tempo definido em download_time_limit
                    print("download attempt ("+str(download_attempt_count)+") failed (download timeout)")
                    download_attempt_count += 1;
                    continue

                if file_size < 1000000:
                    print("file is shorter than 1 MB (may be garbage), ignoring file")
                    os.remove(temp_path+downloaded_file_name)
                    download_attempt_count += 1;
                    continue

                download_success = True

            if download_attempt_count > download_attempt_limit:
                print("all attempts failed, skipping track")
                spotify_playlist_failed_track_names.append(spotify_playlist_track_names[count-1])
                continue

            #sanitiza o nome do arquivo
            if parameter_playlist_id:
                new_file_name = spotify_playlist_track_names[count-1]
                os.rename(temp_path+downloaded_file_name, temp_path+new_file_name+".mp3")
                downloaded_file_name = new_file_name+".mp3"
            else:
                os.rename(temp_path+downloaded_file_name, temp_path+downloaded_file_name.replace('_(MP3Ball.ru)', ''))
                downloaded_file_name = downloaded_file_name.replace('_(MP3Ball.ru)', '')

            beatport_key = get_beatport_key(url_encoded_track_query_string, driver)
            if beatport_key == "key not found":
                print("key info not available on beatport")
            else:
                print("setting tonality ID3 tag ("+beatport_key+") based on beatport key")
                set_file_tkey_tag(temp_path+downloaded_file_name, beatport_key)

            if beatport_key == "key not found": 
                tunebat_key = get_tunebat_key(url_encoded_track_query_string, driver)
                if tunebat_key == "key not found":
                    print("key info not available on tunebat")
                    print("skipping ID3 tagging")
                else:
                    print("setting tonality ID3 tag ("+tunebat_key+") based on tunebat key")
                    set_file_tkey_tag(temp_path+downloaded_file_name, tunebat_key)

        #joga para a pasta de downloaded configurada
        if not skip_download:
            print("moving file '"+temp_path+downloaded_file_name+"' to '"+parameter_download_location+downloaded_file_name+"'")
            shutil.move(temp_path+downloaded_file_name, parameter_download_location+downloaded_file_name)

        #fim da iteração de leitura de linha do arquivo
    if not parameter_playlist_id:
        query_file.close()

    if spotify_playlist_failed_track_names:
        print("WARNING: failed to download the following tracks")
        for failed_track_name in spotify_playlist_failed_track_names:
            print(failed_track_name)
    
    print("script execution ended");
    input("press Enter to exit")
    






