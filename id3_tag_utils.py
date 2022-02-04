from mutagen.id3 import ID3NoHeaderError
from mutagen.id3 import ID3, TIT2, TALB, TPE1, TPE2, COMM, TCOM, TCON, TDRC, TRCK, TKEY

#exemplo: set_file_tkey_tag('C:/Users/Meu computador/Desktop/teste.mp3', u'G')
def set_file_tkey_tag(file_name, key):
    # Read the ID3 tag or create one if not present
    try: 
        tags = ID3(file_name)
    except ID3NoHeaderError:
        print("Adding ID3 header")
        tags = ID3()
##    tags["TIT2"] = TIT2(encoding=3, text=title)
##    tags["TALB"] = TALB(encoding=3, text=u'mutagen Album Name')
##    tags["TPE2"] = TPE2(encoding=3, text=u'mutagen Band')
##    tags["COMM"] = COMM(encoding=3, lang=u'eng', desc='desc', text=u'mutagen comment')
##    tags["TPE1"] = TPE1(encoding=3, text=u'mutagen Artist')
##    tags["TCOM"] = TCOM(encoding=3, text=u'mutagen Composer')
##    tags["TCON"] = TCON(encoding=3, text=u'mutagen Genre')
##    tags["TDRC"] = TDRC(encoding=3, text=u'2010')
##    tags["TRCK"] = TRCK(encoding=3, text=u'track_number')
    tags["TKEY"] = TKEY(encoding=3, text=key)
    tags.save(file_name)


