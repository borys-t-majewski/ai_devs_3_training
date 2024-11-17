def generate_image(client, prompt, model="dall-e-3", size = "1024x1024", quality = "standard", n = 1, preceding_prompt = ''):

    from openai import OpenAI
    response = client.images.generate(
    model=model,
    prompt=preceding_prompt + prompt,
    size=size,
    quality=quality,
    n=n,
    )

    image_url = response.data[0].url
    return image_url