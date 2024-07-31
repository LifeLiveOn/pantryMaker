import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, request

app = Flask(__name__)

# init db
cred = credentials.Certificate('pantry.json')
firebase_admin.initialize_app(cred)

# init firestore
db = firestore.client()


@app.route('/')
def index():
    pantry_ref = db.collection('pantry')
    docs = pantry_ref.stream()
    pantry_ls = [{'id': doc.id, **doc.to_dict()} for doc in docs]
    return render_template('index.html', pantry_ls=pantry_ls)


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

    return "", 404  # 404 Not Found if the item doesn't exist


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

    return "", 404  # 404 Not Found if the item doesn't exist


@app.route('/remove_all/<item_id>', methods=["POST"])
def remove_all(item_id):
    pantry_ref = db.collection("pantry").document(item_id)
    pantry_ref.delete()

    # Return an empty response or a message indicating deletion
    return "", 204  # 204 No Content


@app.route('/add_pantry', methods=["POST"])
def add_pantry():
    data = request.form
    item_name = data['name']
    item_count = int(data['count'])

    # Create a document reference using the name as the document ID
    doc_ref = db.collection('pantry').document(item_name.replace(" ","_"))
    doc = doc_ref.get()

    if doc.exists:
        # If the item already exists, update the count
        existing_data = doc.to_dict()
        new_count = existing_data['count'] + item_count
        doc_ref.update({'count': new_count})
        new_item = {
            'name': item_name,
            'count': new_count,
            'id': item_name.replace(" ","_")
        }
    else:
        # If the item does not exist, create a new document
        new_item = {
            'name': item_name,
            'count': item_count,
            'id': item_name.replace(" ","_")
        }
        doc_ref.set(new_item)
    return render_template('components/item.html', item=new_item)


if __name__ == '__main__':
    app.run()
