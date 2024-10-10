import requests
from bs4 import BeautifulSoup

# Define the URL of the e-commerce site
url = "https://neocomputer.md/gaming-zone"

# Make the GET request
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    print("Successfully retrieved HTML content.")

    # Write the HTML content to a text file
    with open("neocomputer_content.txt", "w", encoding="utf-8") as file:
        file.write(response.text)

    print("HTML content has been written to neocomputer_content.txt.")

    # Now, read from the text file and parse it
    with open("neocomputer_content.txt", "r", encoding="utf-8") as file:
        html_content = file.read()

    # Use Beautiful Soup to parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract product names, prices, and links
    products = []

    for product in soup.find_all(class_='col-lg-4 col-6'):
        link_tag = product.find('a', href=True)
        name_tag = product.find(class_='title')
        price_tag = product.find(class_='price-current')
        description_tag = product.find(class_='excerpt')

        if name_tag and price_tag and link_tag:
            name = name_tag.get_text(strip=True)
            price = price_tag.get_text(strip=True)
            link = link_tag['href']
            description = description_tag.get_text(strip=True)

            products.append({
                'name': name,
                'price': price,
                'link': link,
                'description': description
            })

    # Print extracted products with additional data
    for product in products:
        print(
            f"Product Name: {product['name']}, Price: {product['price']}, Link: {product['link']}, Description: {product['description']}")

else:
    print(f"Failed to retrieve content. Status code: {response.status_code}")
