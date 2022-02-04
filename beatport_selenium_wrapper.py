
def get_beatport_key(url_encoded_track_query_string, driver):
    #pega a tonalidade no beatport
    url = "https://www.google.com/search?q=beatport+"
    url += url_encoded_track_query_string
    print("url: "+url)
    driver.get(url)
    try:
        driver.find_element_by_xpath('(//h3)[1]/../../a').click()
        #na página do beatport, verifica a tonalidade   
    
        beatport_key = driver.find_element_by_class_name('interior-track-key').find_element_by_class_name('value').text

        id3_key = beatport_key.split(" ")[0].replace("♭", "b");
        if beatport_key.split(" ")[1] == "min":
            id3_key += "m"
        id3_key = id3_key.replace("♯","#")
        
        return id3_key
    except Exception:
        return "key not found"
    
