import json
import asyncio
import os
import threading

from flask import Flask, request, jsonify
import psycopg2
from websockets import serve

app = Flask(__name__)

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)

rooms = {}


def insert_product(product):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO products (name, price_mdl, price_eur, link, description)
            VALUES (%s, %s, %s, %s, %s)
        """, (product['name'], product['price_mdl'], product['price_eur'], product['link'], product['description']))
    conn.commit()


def get_products(filters=None, offset=0, limit=5):
    with conn.cursor() as cur:
        query = "SELECT * FROM products"
        params = []

        if filters:
            query += " WHERE " + " AND ".join([f"{key} = %s" for key in filters.keys()])
            params.extend(filters.values())

        query += " OFFSET %s LIMIT %s"
        params.extend([offset, limit])

        cur.execute(query, params)
        return cur.fetchall()


def update_product(product_id, product):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE products 
            SET name = %s, price_mdl = %s, price_eur = %s, link = %s, description = %s 
            WHERE id = %s
        """, (product['name'], product['price_mdl'], product['price_eur'], product['link'], product['description'],
              product_id))
    conn.commit()


def delete_product(product_id):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
    conn.commit()


@app.route('/products', methods=['POST'])
def create_product():
    product = request.json
    insert_product(product)
    return jsonify({"message": "Product created successfully"}), 201


@app.route('/products', methods=['GET'])
def read_products():
    filters = {}
    product_id = request.args.get('id')
    name = request.args.get('name')
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 5))

    if product_id:
        filters['id'] = int(product_id)
    if name:
        filters['name'] = name

    products = get_products(filters, offset, limit)
    return jsonify(products), 200


@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product_route(product_id):
    product = request.json
    update_product(product_id, product)
    return jsonify({"message": "Product updated successfully"}), 200


# Flask route to delete a product by ID (DELETE)
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product_route(product_id):
    delete_product(product_id)
    return jsonify({"message": "Product deleted successfully"}), 204


# Flask route to accept multipart/form-data file uploads (POST)
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == '' or not file.filename.endswith('.json'):
        return jsonify({"error": "Please upload a JSON file"}), 400

    try:
        data = json.load(file)
        if 'products' not in data:
            return jsonify({"error": "Invalid JSON format"}), 400

        for product in data['products']:
            insert_product(product)

        return jsonify({"message": "File uploaded and data inserted successfully"}), 201
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 400


async def handle_client(websocket, path):
    room_name = path.strip("/")
    if room_name not in rooms:
        rooms[room_name] = set()
    rooms[room_name].add(websocket)

    try:
        async for message in websocket:
            print(f"Received message: {message}")

            for client in rooms[room_name]:
                if client != websocket:
                    await client.send(message)
    except Exception as e:
        print(f"Client disconnected from room {room_name}: {e}")
    finally:
        rooms[room_name].remove(websocket)
        if len(rooms[room_name]) == 0:
            del rooms[room_name]


def run_flask_thread():
    app.run(port=5000, debug=True, use_reloader=False)


async def run_websocket():
    async with serve(handle_client, "localhost", 8765):
        print("WebSocket server started on ws://localhost:8765")
        await asyncio.Future()


async def main():
    flask_thread = threading.Thread(target=run_flask_thread)
    flask_thread.start()

    await run_websocket()


# Start both servers
asyncio.run(main())
