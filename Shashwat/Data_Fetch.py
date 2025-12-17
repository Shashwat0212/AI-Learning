import requests

# 1. Set the page title exactly as in the URL
title = "The_Verdict"  # for https://en.wikipedia.org/wiki/The_Verdict

# 2. Call Wikipedia API to get plain-text extract (whole page)
url = "https://en.wikipedia.org/w/api.php"
params = {
    "action": "query",
    "format": "json",
    "titles": title,
    "prop": "extracts",
    "explaintext": True,   # plain text instead of HTML
    # "exintro": True,     # uncomment to get only intro before first heading
}

response = requests.get(url, params=params)
data = response.json()

# 3. Extract page text
page = next(iter(data["query"]["pages"].values()))
text = page["extract"]

# 4. Save to a .txt file
with open("the_verdict_wikipedia.txt", "w", encoding="utf-8") as f:
    f.write(text)

print("Saved to the_verdict_wikipedia.txt")
