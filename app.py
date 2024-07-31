import base64
import io
import os

import requests
from dotenv import load_dotenv
from firebase_admin import credentials, firestore, initialize_app
from flask import Flask, render_template, request

from form import PantryForm

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

cred = credentials.Certificate('pantry.json')
initialize_app(cred)

db = firestore.client()


@app.route('/')
def index():
    form = PantryForm()
    pantry_ref = db.collection('pantry')
    docs = pantry_ref.stream()
    pantry_ls = [{'id': doc.id, **doc.to_dict()} for doc in docs]
    return render_template('index.html', pantry_ls=pantry_ls, form=form)


@app.route('/camera')
def camera():
    return render_template('camera.html')


@app.route('/upload', methods=['POST'])
def upload():
    image_data = request.form['image_data']
    image_data = image_data.split(",")[1]
    image_bytes = base64.b64decode(image_data)

    vertex_ai_url = "https://vertex-ai-endpoint-url"
    headers = {"Authorization": f"Bearer {os.getenv('VERTEX_AI_API_KEY')}"}
    files = {
        'file': ('screenshot.png', io.BytesIO(image_bytes), 'image/png')
    }
    response = requests.post(vertex_ai_url, headers=headers, files=files)
    detected_items = response.json()

    for item in detected_items:
        item_name = item['name']
        item_count = item['count']
        doc_ref = db.collection('pantry').document(item_name.replace(" ", "_"))
        doc = doc_ref.get()
        if doc.exists:
            existing_data = doc.to_dict()
            new_count = existing_data['count'] + item_count
            doc_ref.update({'count': new_count})
        else:
            doc_ref.set({'name': item_name, 'count': item_count})

    return render_template('components/items.html',
                           pantry_ls=detected_items)


@app.route('/decrement/<item_id>', methods=["POST"])
def decrement(item_id):
    pantry_ref = db.collection("pantry").document(item_id)
    doc = pantry_ref.get()

    if doc.exists:
        data = doc.to_dict()
        new_count = data['count'] - 1 if data['count'] > 0 else 0
        pantry_ref.update({'count': new_count})
        data['count'] = new_count
        data['id'] = item_id
        return f"<span id='count-{data['id']}' class='mx-2'>{new_count}</span>"

    return "", 404


@app.route('/increment/<item_id>', methods=["POST"])
def increment(item_id):
    pantry_ref = db.collection("pantry").document(item_id)
    doc = pantry_ref.get()

    if doc.exists:
        data = doc.to_dict()
        new_count = data['count'] + 1
        pantry_ref.update({'count': new_count})
        data['count'] = new_count
        data['id'] = item_id
        return f"<span id='count-{data['id']}' class='mx-2'>{new_count}</span>"

    return "", 404


@app.route('/remove_all/<item_id>', methods=["POST"])
def remove_all(item_id):
    pantry_ref = db.collection("pantry").document(item_id)
    pantry_ref.delete()

    return "", 204


@app.route('/add_pantry', methods=["POST"])
def add_pantry():
    form = PantryForm()
    new_item = None
    if form.validate_on_submit():
        print(form.data)
        item_name = form.data['name']
        item_count = int(form.data['count'])

        doc_ref = db.collection('pantry').document(item_name.replace(" ", "_"))
        doc = doc_ref.get()

        if doc.exists:
            existing_data = doc.to_dict()
            new_count = existing_data['count'] + item_count
            doc_ref.update({'count': new_count})
            new_item = {
                'name': item_name,
                'count': new_count,
                'id': item_name.replace(" ", "_")
            }
        else:
            new_item = {
                'name': item_name,
                'count': item_count,
                'id': item_name.replace(" ", "_")
            }
            doc_ref.set(new_item)
    return render_template('components/item.html', item=new_item, form=form)


if __name__ == '__main__':
    app.run(debug=True)
