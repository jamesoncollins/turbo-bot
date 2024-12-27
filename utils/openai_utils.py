import os
from openai import OpenAI

client = OpenAI(
  api_key=os.environ["OPENAI_API_KEY"]
)

def submit_gpt(query):
    retval = None
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": query
                }
            ]
        )
        print(completion.choices[0].message)
        message = completion.choices[0].message
        content_string = message.content
        retval = content_string
    except:
        pass
    return retval