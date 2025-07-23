import requests 
import json

query = input("Enter the query you want to pass: ")

url = 'http://192.168.220.8:11434/api/generate'
request_body = {
  "model": "llama3",
  "prompt": query,
  "stream": False
}

response = requests.post(url, json=request_body)

if response.status_code == 200:
    response_data = response.json()
    print("\nResponse:")
    print(response_data.get('response', 'No response content found'))
    
    print(f"Error: {response.status_code}")
    print(response.text)