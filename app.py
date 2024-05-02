from flask import Flask, render_template, request, jsonify, redirect, url_for,json
from pymongo import MongoClient
import requests
from datetime import datetime
from bson import ObjectId
import os
from os.path import join, dirname
from dotenv import load_dotenv
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)

db = client[DB_NAME]


app = Flask(__name__)



@app.route('/')
def main():
    words_result = db.words.find({}, {'_id': False})
    words = []
    for word in words_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,
        })
    msg = request.args.get('msg')
    return render_template('index.html',words=words,msg=msg)


@app.route('/detail/<keyword>')
def detail(keyword):
    api_key = 'b7226263-e4db-4cb9-b67e-c59c187a6987'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definitions = response.json()
    
    if not definitions:
        return render_template('eror.html',msg=f'Could not find {keyword}')

    if type(definitions[0]) is str:
        return render_template('eror.html',msg=f'Could not find {keyword}',definitions=definitions
        )
    return render_template('detail.html',word=keyword,definitions=definitions,status=request.args.get('status_give', 'new')
    )


@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')
    doc = {
        'word': word,
        'definitions': definitions,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    db.words.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'the word, {word}, was saved!!!',
    })


@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    word = request.form.get('word_give')
    db.words.delete_one({'word': word})
    db.examples.delete_many({'word': word})
    return jsonify({
        'result': 'success',
        'msg': f'the word {word} was deleted'
    })
    
@app.route('/api/get_exs', methods=['GET'])
def get_exs():
    word = request.args.get('word_give')
    example_data = db.examples.find({"word":word})
    array = []
    for example in example_data:
        array.append({
            'example': example.get('example'),
            'id': str(example.get('_id'))
        })    
    return jsonify({'result': 'success'
                    ,'examples': array})

@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    word = request.form.get('word_give')
    example_give = request.form.get('example_give')
    data = {
        'word': word,
        'example': example_give
    }
    db.examples.insert_one(data)
    return jsonify({'result': 'success',
                    'msg': f"The {word}'s example was saved!"
                    })
                    


@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
    word = request.form.get('word')
    id = request.form.get('id')
    db.examples.delete_one({'_id': ObjectId(id)})
    return jsonify({'result': 'delete Success',
                    'msg': f'The {word} example was deleted!'
                    })


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)