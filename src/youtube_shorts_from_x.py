import requests

r = requests.get("https://nitter.space/editsgoeshard")
print(r.text)
