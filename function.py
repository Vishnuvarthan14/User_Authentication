import requests
import urllib.parse
from flask import jsonify
base='http://127.0.0.1:5000'
mail = 'jvishnuvarthan2005@gmail.com'
def getDetails(email):
    refined_mail = urllib.parse.quote(email)
    datas = requests.get(f'{base}/get/{refined_mail}')
    return datas.json()

def authenticate(email,password):
    og_data=getDetails(email)
    if(og_data['password']==password):
        return {'message':'Success'}
    else:
        return {'message':'Invalid email or password'}
