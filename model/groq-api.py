import os
import requests
from groq import Groq
from dotenv import load_dotenv 


load_dotenv()


query = input("Enter the query you want to pass: ")

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": query,
        }
    ],
    model="llama-3.3-70b-versatile",
)

print(chat_completion.choices[0].message.content)