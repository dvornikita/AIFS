import os
import base64
import requests
from prompts import get_image_captioning_instructions, get_image_recognition_instructions


def caption_image(image_path=None, image_url=None, api_key=None, mode="caption"):
    assert image_path is not None or image_url is not None, "Either image_path or image_url should be provided."
    assert image_path is None or image_url is None, "Only one of image_path or image_url should be provided."

    # OpenAI API Key
    api_key = api_key or os.getenv("OPENAI_API_KEY")

    if image_path is not None:
        # Function to encode the image
        def encode_image(image_path):
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")

        # Getting the base64 string
        base64_image = encode_image(image_path)
        image_url = f"data:image/jpeg;base64,{base64_image}"

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    prompt = get_image_captioning_instructions() if mode == "caption" else get_image_recognition_instructions()
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url, "detail": "low"},
                    },
                ],
            }
        ],
        "max_tokens": 300,
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload).json()
    caption = response["choices"][0]["message"]["content"]
    if mode != "caption":
        return caption.lower().strip().rstrip(".")
    return caption
