import requests
import openai
import os
import asyncio
from openai import AsyncOpenAI
url = "http://127.0.0.1:5000/v1/chat/completions"
openai.api_key = "..."
openai.api_base = "http://127.0.0.1:5000/v1"
openai.api_version = "2023-05-15"
from openai import OpenAI
client = OpenAI(
    # This is the default and can be omitted
    api_key="...",
    base_url="http://127.0.0.1:5000/v1",
)
def Generate(content):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
        model="null",)
    response = chat_completion.choices[0]
    return response.message.content