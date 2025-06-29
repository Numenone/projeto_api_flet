import json
from datetime import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)

# Dados iniciais
data = {
    "products": [
        {
            "id": 1,
            "name": "Notebook Dell",
            "price": 4500.00,
            "quantity": 10,
            "categoryId": 1,
            "createdAt": datetime.now().isoformat()
        },
        {
            "id": 2,
            "name": "iPhone 13",
            "price": 6000.00,
            "quantity": 15,
            "categoryId": 2,
            "createdAt": datetime.now().isoformat()
        },
        {
            "id": 3,
            "name": "Monitor LG",
            "price": 1200.00,
            "quantity": 8,
            "categoryId": 3,
            "createdAt": datetime.now().isoformat()
        }
    ],
    "categories": [
        {"id": 1, "name": "Notebooks"},
        {"id": 2, "name": "Celulares"},
        {"id": 3, "name": "Monitores"}
    ]
}

# Salva os dados iniciais em um arquivo JSON
with open('db.json', 'w') as f:
    json.dump(data, f, indent=2)

# Rotas da API
@app.route('/products', methods=['GET'])
def get_products():
    return jsonify(data['products'])

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = next((p for p in data['products'] if p['id'] == product_id), None)
    if product:
        return jsonify(product)
    return jsonify({"error": "Product not found"}), 404

@app.route('/products', methods=['POST'])
def create_product():
    new_product = request.get_json()
    new_product['id'] = max(p['id'] for p in data['products']) + 1
    new_product['createdAt'] = datetime.now().isoformat()
    data['products'].append(new_product)
    
    # Atualiza o arquivo db.json
    with open('db.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    return jsonify(new_product), 201

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = next((p for p in data['products'] if p['id'] == product_id), None)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    updated_data = request.get_json()
    product.update(updated_data)
    
    # Atualiza o arquivo db.json
    with open('db.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    return jsonify(product)

@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    global data
    data['products'] = [p for p in data['products'] if p['id'] != product_id]
    
    # Atualiza o arquivo db.json
    with open('db.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    return jsonify({"message": "Product deleted"}), 200

@app.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(data['categories'])

@app.route('/categories', methods=['POST'])
def create_category():
    new_category = request.get_json()
    if not data['categories']:
        new_category['id'] = 1
    else:
        new_category['id'] = max(c['id'] for c in data['categories']) + 1
    data['categories'].append(new_category)
    
    # Atualiza o arquivo db.json
    with open('db.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    return jsonify(new_category), 201

if __name__ == '__main__':
    app.run(port=3000, debug=True)