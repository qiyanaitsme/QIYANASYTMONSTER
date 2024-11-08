import aiohttp
import urllib.parse

async def get_balance(api_token):
    post = {
        "action": "user-balance",
        "token": api_token
    }

    post_data = "&".join([f"{key}={urllib.parse.quote(str(value))}" for key, value in post.items()])

    headers = {
        "User-Agent": "Mozilla/4.0 (compatible; MSIE 5.00; Windows NT 5.0)",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.clifl.com/",
                headers=headers,
                data=post_data,
                ssl=False,
                allow_redirects=True
            ) as response:
                text = await response.text()
                import json
                result = json.loads(text)
                if result['status'] == 'success':
                    actual_balance = result['response']['coin'] - 69030
                    return f"Монет: {actual_balance}"
                return "Монет: 0"

    except Exception as e:
        return "Монет: 0"
