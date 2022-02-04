from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def get_tunebat_key(url_encoded_track_query_string, driver):
##    caps = DesiredCapabilities().FIREFOX
##    caps["pageLoadStrategy"] = "eager"
##    driver = webdriver.Firefox(capabilities=caps, firefox_binary=binary, executable_path="C:\\Utility\\BrowserDrivers\\geckodriver.exe")
##    driver.get("https://google.com")
   
    #pega a tonalidade no tunebat
    url = "https://tunebat.com/Search?q="
    url += url_encoded_track_query_string
    print("url: "+url)
    driver.get(url)

    #na página do tunebat, verifica a tonalidade   
    try:
        #achar uma tag p escrito key
        #pegar texto da tag p anterior
        #key = driver.find_element_by_class_name('interior-track-key').find_element_by_class_name('value').text

        print("waiting for element 1")
        #div com class ant-col
        key_element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located( (By.XPATH,'//p[normalize-space(text())="Key"]')))
        print("waiting for element 2")
        #key_element2 = (By.XPATH,'//p[normalize-space(text())="Key"]/preceding')[0]
        key_element2 = driver.find_element(By.XPATH, '//p[normalize-space(text())="Key"]/preceding::*[1]')
        
        print(key_element2)
        key = key_element2.text
        print(key)

        id3_key = key.split(" ")[0].replace("♭", "b");
        if key.split(" ")[1] == "Minor":
            id3_key += "m"
        id3_key = id3_key.replace("♯","#")

        print(id3_key)
        return id3_key
    except Exception as e:
        print(str(e))
        return "key not found"


    
