import re # Регулярные выражения.
import requests # Загрузка новостей с сайта.
from bs4 import BeautifulSoup # Превращалка html в текст.
import pymorphy2 # Морфологический анализатор.
import datetime # Новости будем перебирать по дате.
from collections import Counter # Не считать же частоты самим.
import math # Корень квадратный.

class getNewsPaper:
    articles=[]     # Загруженные статьи.
    dictionaries=[] # Посчитанные словари (векторное представление статей).
        
    # Конструктор - компилирует регулярные выражения и загружает морфологию.
    def __init__(self):
        self.delscript = re.compile("<script.*?>.+?</script>", re.S)
        self.findheaders = re.compile("<h1.+?>(.+)</h1>", re.S)
        self.boa = re.compile('<div class="b-text clearfix js-topic__text" itemprop="articleBody">', re.S)
        self.eoa = re.compile('<div class="b-box">\s*?<i>', re.S)
        self.findURLs = re.compile('<h3>(.+?)</h3>', re.S)
        self.rboa = re.compile('<p class="MegaArticleBody_first-p_2htdt">', re.S)
        self.reoa = re.compile('<div class="Attribution_container_28wm1">', re.S)
        self.rfindURLs = re.compile('''<div class="headlineMed"><a href='(.+?)'>''', re.S)
        # Создаем и загружаем морфологический словарь.
        self.morph=pymorphy2.MorphAnalyzer()

    # Загрузка статьи по URL.
    def getLentaArticle(self, url):
        """ getLentaArticle gets the body of an article from Lenta.ru"""
        # Получает текст страницы.
        art=requests.get(url)
        # Находим заголовок.
        title = findheaders.findall(art.text)[0]
        # Выделяем текст новости.
        bs=BeautifulSoup(art.text, "lxml")
        # Выкусываем скрипты - BeautifulSoup не справляетсяя с ними. bs['p'] выделяет параграфы текста.
        # [1:-1] применяется ля того, чтобы выкусить квадратные скобки, которые добавляются здесь при преобразовании к строке.
        text=delscript.split(str(bs('p'))[1:-1])
        # Выкусываем остальные теги.
        self.articles.append(BeautifulSoup(title+"\n-----\n"+" ".join(text), "lxml").get_text())

    # Загрузка всех статей за один день.
    def getLentaDay(self, url):
        """ Gets all URLs for a given day and gets all texts. """
        try:
            day = requests.get(url) # Грузим страницу со списком всех статей.
            cand = self.findURLs.findall(day.text) # Выделяем адреса статей.
            links = ['https://lenta.ru'+re.findall('"(.+?)"', x)[0] for x in cand]
            for l in links: # Загружаем статьи.
                self.getLentaArticle(l)
        except:
            pass

    # Загрузка всех статей за несколько дней.
    def getLentaPeriod(self, start, finish):
        curdate=start
        while curdate<=finish:
            print(curdate.strftime('%Y/%m/%d')) # Just in case.
            # Список статей грузится с вот такого адреса.
            res=self.getLentaDay('https://lenta.ru/news/'+curdate.strftime('%Y/%m/%d'))
            curdate+=datetime.timedelta(days=1)
      
    # Потроение вектора для статьи.
    posConv={'ADJF':'_ADJ','NOUN':'_NOUN','VERB':'_VERB'}
    def getArticleDictionary(self, text, needPos=None):
        words=[a[0] for a in re.findall("([А-ЯЁа-яё]+(-[А-ЯЁа-яё]+)*)", text)]
        reswords=[]
    
        for w in words:
            wordform=self.morph.parse(w)[0]
            try:
                if wordform.tag.POS in ['ADJF', 'NOUN', 'VERB']:
                    if needPos!=None:
                        reswords.append(wordform.normal_form+self.posConv[wordform.tag.POS])
                    else:
                        reswords.append(wordform.normal_form)
            except:
                pass
            
        stat=Counter(reswords)
#        stat={a: stat[a] for a in stat.keys() if stat[a]>1}
        return stat

    # Посчитаем вектора для всех статей.
    def calcArticleDictionaries(self, needPos=None):
        self.dictionaries=[]
        for a in self.articles:
            self.dictionaries.append(self.getArticleDictionary(a, needPos))

    # Сохраняем стстьи в файл.
    def saveArticles(self, filename):
        """ Saves all articles to a file with a filename. """
        newsfile=open(filename, "w")
        for art in self.articles:
            newsfile.write('\n=====\n'+art)
        newsfile.close()

    # Читаем статьи из файла.
    def loadArticles(self, filename):
        """ Loads and replaces all articles from a file with a filename. """
        newsfile=open(filename, encoding="utf-8")
        text=newsfile.read()
        self.articles=text.split('\n=====\n')[1:]
#        self.articles=[a.replace('\xa0', ' ') for a in text.split('\n=====\n')[1:]]
        newsfile.close()

    # Для удобства - поиск статьи по ее заголовку.
    def findNewsByTitle(self, title):
        for i, a in enumerate(self.articles):
            if title==a.split('\n-----\n')[0]:
                return i
        return -1

def cosineSimilarity(a, b):
    if len(a.keys())==0 or len(b.keys())==0:
        return 0
    sumab=sum([a[na]*b[na] for na in a.keys() if na in b.keys()])
    suma2=sum([a[na]*a[na] for na in a.keys()])
    sumb2=sum([b[nb]*b[nb] for nb in b.keys()])
    return sumab/math.sqrt(suma2*sumb2)

