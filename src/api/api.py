import os
import json
import requests
from flask import Blueprint, jsonify
from datetime import datetime
from models import *
from operator import attrgetter

NEWS_API_KEY = os.getenv('GOOGLE_NEWS_API_KEY')
api = Blueprint('api', __name__, url_prefix='/api')

#Retornar um json com todos os jsons de deputados
@api.route('/deputies')
def index():
    full_json = []

    for item in Deputy.objects:
        full_json.append(item.to_json())

    return jsonify(full_json)


@api.route('/deputy/<id>')
def deputy(id):
    for deputy in Deputy.objects:
        if int(deputy.id) == int(id):
            return deputy.to_json()

    return {}

#Pegar as duas noticias mais recentes do nosso banco de dados
@api.route('/news')
def news():
    all_news = News.objects
    
    #Ordenar a lista de acordo com a data.
    sorted_list = sorted(all_news, key=attrgetter('update_date'), reverse = True)
    news_list = []
    for item in sorted_list[0:2]:
        news_list.append(item.to_json())

    return jsonify(news_list)

@api.route('/all_news')
def all_news():
    all_news = []
    for item in News.objects:
        all_news.append(item.to_json())

    return jsonify(all_news)

#Atualizar as noticias do banco de dado de acordo com a API Google News
@api.route('/limpar_noticias')
def limpar_noticias():
    News.objects.all().delete()
    return str(len(News.objects))

#Atualizar as noticias do banco de dado de acordo com a API Google News
@api.route('/atualizar_noticias')
def atualizar_noticias():
    #criar o resquest para pegar todas as noticiar relacionadas a deputado(a) e montar um json
    r = requests.get(f'https://newsapi.org/v2/everything?q=deputado OR deputada&language=pt&sortby=publishedAt&pageSize=100&apiKey={NEWS_API_KEY}')
    all_news_json = r.json()["articles"]
    #pegar qual foi o ultimo id no banco
    last_id = 0

    if len(News.objects) is 0:
        last_id = 0
    else:
        last_id = News.objects().order_by('id')[0].id

    #criar uma lista com todos os objetos para nao usar o QueryType
    all_news_list = []
    for item in News.objects:
        all_news_list.append(item)
    
    #para cada json na lista de todos os jsons, iterar para saber se é uma noticia de algum deputado em questão.
    for item in all_news_json:
        old_news = News.objects(abstract=item["description"]).first()
        if old_news:
            continue

        published_new_date = str(item["publishedAt"])
        news_date = news_date = datetime.strptime(published_new_date, "%Y-%m-%dT%H:%M:%SZ") if len(str(item["publishedAt"])) > 4 else None

        #acessar cada deputado para bverificar se o nome dele está em algum item do json da noticia
        for deputy in Deputy.objects:
            if (deputy.name in item["content"]) or (deputy.name in item["description"]) or (deputy.name in item["title"]):
                
                last_id = last_id + 1
                populate_news_1 = News(
                id=last_id,
                deputy_id=deputy.id,
                link=item["url"] if item["url"] is not None else None,
                photo=item["urlToImage"] if item["urlToImage"] is not None else None,
                title=item["title"] if item["title"] is not None else None,
                abstract=item["description"] if item["description"] is not None else None,
                deputy_name=deputy.name,
                update_date=news_date,
                source=item["source"]["name"]
                ).save()

                #atualizar a ultima atividade recente envolvendo esse deputado
                deputy.last_activity_date = news_date
                deputy.save()

    #cria uma nova lista com todos os objetos criados de noticia para transformá-lo em uma lista de json
    return "Done. Use /all_news to get all news in data base."

@api.route('/get_news_by_id/<id>')
def get_news_by_id(id):
    news_list = list(News.objects(deputy_id=id).all())
    return_json_list = []
    for item in news_list:
        return_json_list.append(item.to_json())
    
    return jsonify(return_json_list)