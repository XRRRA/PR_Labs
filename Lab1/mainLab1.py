import socket
import ssl
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from functools import reduce

# Define the URL and port for HTTPS
url = "neocomputer.md"
port = 443

# Create an SSL context
context = ssl.create_default_context()

# Create a TCP socket and wrap it in SSL
sock = socket.create_connection((url, port))
wrapped_socket = context.wrap_socket(sock, server_hostname=url)

# Prepare and send the HTTP GET request
http_request = f"GET /gaming-zone HTTP/1.1\r\nHost: {url}\r\nConnection: close\r\n\r\n"
wrapped_socket.sendall(http_request.encode())

# Receive the response
response = b""
while True:
    part = wrapped_socket.recv(4096)
    if not part:
        break
    response += part

# Close the socket connection
wrapped_socket.close()

# Decode the response and split headers from body
response_str = response.decode()
headers, html_content = response_str.split("\r\n\r\n", 1)

# Use Beautiful Soup to parse the HTML content
soup = BeautifulSoup(html_content, 'html.parser')

# Extract product names, prices, and links
products = []

for product in soup.find_all(class_='col-lg-4 col-6'):
    link_tag = product.find('a', href=True)
    name_tag = product.find(class_='title')
    price_tag = product.find(class_='price-current')
    description_tag = product.find(class_='excerpt')

    if name_tag and price_tag and link_tag:
        # Remove whitespaces from name and description
        name = name_tag.get_text(strip=True)
        description = description_tag.get_text(strip=True) if description_tag else "No description available"

        # Extract and validate price
        price_str = price_tag.get_text(strip=True).replace('lei', '').replace(' ', '')

        try:
            price_mdl = int(price_str)
        except ValueError:
            print(f"Invalid price format for {name}. Skipping this product.")
            continue

        link = link_tag['href']

        products.append({
            'name': name,
            'price_mdl': price_mdl,
            'link': link,
            'description': description
        })

mdl_to_eur_rate = 0.05

for product in products:
    print(
        f"Product Name: {product['name']}, Price (MDL): {product['price_mdl']}, Link: {product['link']}, Description: {product['description']}")
    product['price_eur'] = round(product['price_mdl'] * mdl_to_eur_rate, 2)

# Filter: Define a price range (in EUR)
min_price_eur = 500.0
max_price_eur = 3000.0

filtered_products = list(filter(lambda p: min_price_eur <= p.get('price_eur', 0) <= max_price_eur, products))

# Reduce: Sum up the prices of filtered products (in EUR)
total_price_eur = reduce(lambda acc, p: acc + p['price_eur'], filtered_products, 0)

result_summary = {
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'total_price_eur': total_price_eur,
    'filtered_products': filtered_products,
}

# Print result summary
print(f"Total Price (EUR): {result_summary['total_price_eur']}")
print("Filtered Products:")
for product in result_summary['filtered_products']:
    print(f"Product Name: {product['name']}, Price (EUR): {product['price_eur']}, Link: {product['link']}")
