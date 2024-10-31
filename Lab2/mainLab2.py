import json
from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

# PostgreSQL's connection settings
conn = psycopg2.connect(
    dbname="prlab2_db",
    user="postgres",
    password="liviuiordan03",
    host="localhost",
    port="5432"
)


# Function to insert a product
def insert_product(product):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO products (name, price_mdl, price_eur, link, description)
            VALUES (%s, %s, %s, %s, %s)
        """, (product['name'], product['price_mdl'], product['price_eur'], product['link'], product['description']))
    conn.commit()


# Function to retrieve products with optional filters, has task 4: pagination
def get_products(filters=None, offset=0, limit=5):
    with conn.cursor() as cur:
        query = "SELECT * FROM products"
        params = []

        # Add filters if provided
        if filters:
            query += " WHERE " + " AND ".join([f"{key} = %s" for key in filters.keys()])
            params.extend(filters.values())

        # Add pagination
        query += " OFFSET %s LIMIT %s"
        params.extend([offset, limit])

        cur.execute(query, params)
        return cur.fetchall()


# Function to update a product by ID
def update_product(product_id, product):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE products 
            SET name = %s, price_mdl = %s, price_eur = %s, link = %s, description = %s 
            WHERE id = %s
        """, (product['name'], product['price_mdl'], product['price_eur'], product['link'], product['description'],
              product_id))
    conn.commit()


# Function to delete a product by ID
def delete_product(product_id):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
    conn.commit()


# Route to create a new product (POST)
@app.route('/products', methods=['POST'])
def create_product():
    product = request.json
    insert_product(product)
    return jsonify({"message": "Product created successfully"}), 201


# Route to read products with optional query parameters (GET), has task 4: pagination
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


# Route to update a product by ID (PUT)
@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product_route(product_id):
    product = request.json
    update_product(product_id, product)
    return jsonify({"message": "Product updated successfully"}), 200


# Route to delete a product by ID (DELETE)
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product_route(product_id):
    delete_product(product_id)
    return jsonify({"message": "Product deleted successfully"}), 204


# Task 5: Route to accept multipart/form-data file uploads (POST)
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    # Ensure the file is a JSON file
    if file.filename == '' or not file.filename.endswith('.json'):
        return jsonify({"error": "Please upload a JSON file"}), 400

    # Load and insert JSON data into the database
    try:
        data = json.load(file)
        if 'products' not in data:
            return jsonify({"error": "Invalid JSON format"}), 400

        for product in data['products']:
            insert_product(product)

        return jsonify({"message": "File uploaded and data inserted successfully"}), 201
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON file"}), 400


# Run the application
if __name__ == '__main__':
    app.run(debug=True)
