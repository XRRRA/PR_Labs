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

    # Extract product names and prices
    products = []

    # Adjust these selectors based on actual HTML structure
    for product in soup.find_all(class_='product-wrap'):
        name_tag = product.find(class_='title')
        price_tag = product.find(class_='price-current')

        if name_tag and price_tag:
            name = name_tag.get_text(strip=True)
            price = price_tag.get_text(strip=True)
            products.append({'name': name, 'price': price})

    # Print extracted products
    for product in products:
        print(f"Product Name: {product['name']}, Price: {product['price']}")

else:
    print(f"Failed to retrieve content. Status code: {response.status_code}")
