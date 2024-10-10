import requests

# Define the URL of the e-commerce site
url = "https://neocomputer.md/"

# Make the GET request
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    print("Successfully retrieved HTML content.")
    # Print the first 500 characters of the HTML content
    print(response.text[:500])  # Displaying only a portion for brevity
else:
    print(f"Failed to retrieve content. Status code: {response.status_code}")