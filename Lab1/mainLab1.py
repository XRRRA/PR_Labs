import socket
import ssl
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from functools import reduce

url = "neocomputer.md"
port = 443

context = ssl.create_default_context()

sock = socket.create_connection((url, port))
wrapped_socket = context.wrap_socket(sock, server_hostname=url)

http_request = f"GET / HTTP/1.1\r\nHost: {url}\r\nConnection: close\r\n\r\n"
wrapped_socket.sendall(http_request.encode())

response = b""
while True:
    part = wrapped_socket.recv(4096)
    if not part:
        break
    response += part

wrapped_socket.close()

response_str = response.decode()
headers, html_content = response_str.split("\r\n\r\n", 1)

soup = BeautifulSoup(html_content, 'html.parser')

gaming_zone_link_tag = soup.find('a', href="gaming-zone", class_='btn-menu dropbtn label')

if gaming_zone_link_tag:
    gaming_zone_path = gaming_zone_link_tag['href']  # Get the href value
    gaming_zone_url = f"/{gaming_zone_path.lstrip('/')}"

    sock = socket.create_connection((url, port))
    wrapped_socket = context.wrap_socket(sock, server_hostname=url)

    http_request = f"GET {gaming_zone_url} HTTP/1.1\r\nHost: {url}\r\nConnection: close\r\n\r\n"
    wrapped_socket.sendall(http_request.encode())

    response = b""
    while True:
        part = wrapped_socket.recv(4096)
        if not part:
            break
        response += part

    wrapped_socket.close()

    response_str = response.decode()
    headers, html_content = response_str.split("\r\n\r\n", 1)

    soup = BeautifulSoup(html_content, 'html.parser')

products = []

for product in soup.find_all(class_='col-lg-4 col-6'):
    link_tag = product.find('a', href=True)
    name_tag = product.find(class_='title')
    price_tag = product.find(class_='price-current')
    description_tag = product.find(class_='excerpt')

    if name_tag and price_tag and link_tag:
        name = name_tag.get_text(strip=True)  # Validation1 remove whitespace from the product name
        description = description_tag.get_text(strip=True) if description_tag else "No description available"

        price_str = price_tag.get_text(strip=True).replace('lei', '').replace(' ', '')

        try:
            price_mdl = int(price_str)  # Validation 2 converts to integer; raises ValueError if not valid
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
    product['price_eur'] = round(product['price_mdl'] * mdl_to_eur_rate, 2)

min_price_eur = 500.0
max_price_eur = 3000.0

filtered_products = list(filter(lambda p: min_price_eur <= p.get('price_eur', 0) <= max_price_eur, products))

total_price_eur = reduce(lambda acc, p: acc + p['price_eur'], filtered_products, 0)

result_summary = {
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'total_price_eur': total_price_eur,
    'filtered_products': filtered_products,
}


def serialize_to_json(data):
    json_string = "{\n"
    json_string += '  "products": [\n'

    items = []
    for product in data:
        item = (
            f'    {{\n'
            f'      "name": "{product["name"]}",\n'
            f'      "price_mdl": {product["price_mdl"]},\n'
            f'      "price_eur": {product["price_eur"]},\n'
            f'      "link": "{product["link"]}",\n'
            f'      "description": "{product["description"]}"\n'
            f'    }}'
        )
        items.append(item)

    json_string += ',\n'.join(items)
    json_string += '\n  ]\n'
    json_string += '}'

    return json_string


def serialize_to_xml(data):
    xml_string = "<products>"

    for product in data:
        xml_string += f"""
        <product>
            <name>{product['name']}</name>
            <price_mdl>{product['price_mdl']}</price_mdl>
            <price_eur>{product['price_eur']}</price_eur>
            <link>{product['link']}</link>
            <description>{product['description']}</description>
        </product>"""

    xml_string += "</products>"
    return xml_string


json_output = serialize_to_json(result_summary['filtered_products'])
xml_output = serialize_to_xml(result_summary['filtered_products'])

with open("serialization_json.json", "w", encoding="utf-8") as json_file:
    json_file.write(json_output)

print("Serialized JSON saved to serialization_json.txt")

with open("serialization_xml.xml", "w", encoding="utf-8") as xml_file:
    xml_file.write(xml_output)

print("Serialized XML saved to serialization_xml.txt")


def generic_serialize(data, indent_level=0):
    indent_space = '  ' * indent_level
    if isinstance(data, dict):
        items = [f'\n{indent_space}D: k: str({key}): v: {generic_serialize(value, indent_level + 1)}' for key, value in
                 data.items()]
        return f'D:[{",".join(items)}\n{indent_space}]'
    elif isinstance(data, list):
        items = [generic_serialize(item, indent_level) for item in data]
        return f'L:[{",".join(items)}]'
    elif isinstance(data, str):
        return f'str("{data.replace(",", "/")}")'
    elif isinstance(data, int):
        return f'int({data})'
    elif isinstance(data, float):
        return f'float({data})'
    else:
        return 'unknown_type'


def generic_deserialize(serialized_data):
    serialized_data = serialized_data.strip()

    if serialized_data.startswith('D:'):
        content = serialized_data[2:-1]
        items = []

        in_string = False
        current_item = []

        for char in content:
            if char == '"' and (not current_item or current_item[-1] != '\\'):
                in_string = not in_string
            if char == ',' and not in_string:
                items.append(''.join(current_item).strip())
                current_item = []
            else:
                current_item.append(char)

        if current_item:
            items.append(''.join(current_item).strip())

        result = {}
        for item in items:
            key_value = item.split(': v:')
            if len(key_value) != 2:
                print(f"Skipping malformed entry: {item}")
                continue

            key = key_value[0].split('str(')[1][:-1].replace('\\"', '"')
            value = generic_deserialize(key_value[1].strip())
            result[key] = value
        return result

    elif serialized_data.startswith('L:'):
        content = serialized_data[2:-1]
        items = content.split(',')
        return [generic_deserialize(item.strip()) for item in items]

    elif serialized_data.startswith('str("'):
        return serialized_data[5:].replace('/,',
                                           ',')

    elif serialized_data.startswith('int('):
        return int(serialized_data[4:])

    elif serialized_data.startswith('float('):
        return float(serialized_data[6:-1])

    else:
        print(f"Unknown type encountered: {serialized_data}")
        return None


serialized_data = generic_serialize(filtered_products)

with open("serialized_data.txt", "wb") as file:
    file.write(serialized_data.encode('utf-8'))

print("Serialized data saved to serialized_data.txt")

deserialized_products = generic_deserialize(serialized_data)

print("\nDeserialized Products:")
for product in deserialized_products:
    print(product)
