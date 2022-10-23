from unidecode import unidecode 
from flask import Flask,request,jsonify
from flasgger import Swagger, LazyString, LazyJSONEncoder, swag_from
from nltk.tokenize import WordPunctTokenizer
import pandas as pd
import re
import sqlite3 as sq
import time

app=Flask(__name__)
app.json_encoder = LazyJSONEncoder

swagger_template = dict(
info = {
    'title': LazyString(lambda: 'API Documentation for Data Cleansing'),
    'version': LazyString(lambda: '1.0.0'),
    'description': LazyString(lambda: 'Dokumentasi untuk Data Cleansing'),
    },
    host = LazyString(lambda: request.host)
)

swagger_config_text = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

swagger = Swagger(app, template=swagger_template,             
                  config=swagger_config_text)

#Data Cleansing
def remove_emoticon(text):
# return re.sub(r"[^\x00-\x7F]+", " ", text)
  return unidecode(text)

def remove_emoticon2(text):
    return re.sub(r"\\x[A-Za-z0-9./]+", " ", text)

def remove_space(text):
    return re.sub(' +',' ',text)
       
def remove_backslashn(text):
    return re.sub(r"\\n+", "  ", text)

def remove_punctuation(text):
    user_removed = re.sub(r'@[A-Za-z0-9]+','',text)
    link_removed = re.sub('https?://[A-Za-z0-9./]+','',user_removed)
    only_alphanumeric = re.sub('[^a-zA-Z0-9]', ' ', user_removed)
    lower_case_tweet = only_alphanumeric.lower()
    tok = WordPunctTokenizer()
    words = tok.tokenize(lower_case_tweet)
    remove_punctuation = (' '.join(words)).strip()
    return remove_punctuation

def remove_hastag(text):
    return re.sub("#[^\s]+","",text)

@swag_from("swagger_config_text.yml", methods =  ['POST'])           
@app.route("/project_gold_text", methods = ['POST']) 
def cleansing_text():
    text = request.get_json()
    no_emoticon = remove_emoticon(text['text'])
    no_emoticon2 = remove_emoticon2(no_emoticon)
    no_space = remove_space(no_emoticon2)
    no_slashn = remove_backslashn(no_space)
    non_punct = remove_punctuation(no_slashn)
    no_hashtag = remove_hastag(non_punct)
    hasil = {
       "result" : no_hashtag
    }
    
    #import to db
    conn = sq.connect("data_tweet1.db")  
    conn.execute("insert into tweet (Dirty_text,Clean_text) values (?,?)", (text['text'],no_hashtag)) 
    conn.commit()
    conn.close()

    return jsonify(hasil)


@swag_from("swagger_config_file.yml", methods = ['POST'])           
@app.route("/project_gold_file", methods = ['POST']) 
def post_file():
    file = request.files["file"]
    start = time.time()
    df = pd.read_csv(file, encoding ="latin1")
    df['new_Tweet'] = df['Tweet'].str.lower()
    df['new_Tweet'] = df['new_Tweet'].replace('user','',regex=True)
    df['new_Tweet'] = df['new_Tweet'].apply(remove_emoticon)
    df['new_Tweet'] = df['new_Tweet'].apply(remove_emoticon2)
    df['new_Tweet'] = df['new_Tweet'].apply(remove_space)
    df['new_Tweet'] = df['new_Tweet'].apply(remove_backslashn)
    df['new_Tweet'] = df['new_Tweet'].apply(remove_punctuation)
    df['new_Tweet'] = df['new_Tweet'].apply(remove_hastag)
    print(df.head(6))
    
    #import to database
    data = df
    sql_data = 'DATA_TWEET'
    conn = sq.connect(sql_data)
    mycur = conn.cursor
    
    data.to_sql('DATA_TWEET',conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()
    end = time.time()

    hasil = {
       "result" : "succesfully uploaded to db",
       "time execution" : end - start
    }
    
    return jsonify(hasil)

if __name__ == "__main__":
        app.run(port=1255, debug = True)


