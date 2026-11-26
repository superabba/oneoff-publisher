import json, re, sys, collections
raw = open(sys.argv[1], encoding="utf-8").read()
text = json.loads(raw)["content"] if sys.argv[1].endswith(".json") else raw
key = sys.argv[2].strip()
body = re.sub(r"!\[[^\]]*\]\(media:[^)]*\)", " ", text)
html = re.findall(r"</?[A-Za-z][^<>]*>|<!--|&(?:[A-Za-z]+|#\d+);", body)
links = re.findall(r"https?://\S+|www\.\S+|\]\([^)]*\)|@video[^\n]*|(?:[A-Za-z0-9-]+\.)+(?:com|net|org|kr|io|be|ly|me)(?![A-Za-z])", body)
plain = re.sub(r"\{[.#][^}\n]*\}", " ", body)
josa = re.compile(r"(?:으로부터|에서는|에서도|에게는|으로는|으로도|이라는|이라면|까지는|부터는|에서|에게|으로|까지|부터|보다|처럼|마다|이나|이란|이며|이고|라는|하고|에는|에도|와는|과는|은|는|이|가|을|를|의|에|도|만|로|와|과)$")
skip = set("수 것 등 때 더 이 그 저 및 안 못 할 한 두 세 있 있다 있는 있어 있습니다 없는 없다 합니다 하는 해야 됩니다 되는 경우 위해 대한 통해 또는 그리고 하지만 따라 때문".split())
words = collections.Counter()
for w in re.findall(r"[가-힣A-Za-z]+", plain):
    s = josa.sub("", w)
    if len(s) < 2:
        s = w
    s = re.sub(r"(?<=..)들$", "", s)
    if s not in skip:
        words[s] += 1
over = [(w, n) for w, n in words.most_common() if n >= 5]
hits = plain.count(key)
for name, bad in (("HTML", html), ("링크", links), ("5회 이상 단어", over)):
    print(f"{name}: {bad if bad else '없음'}")
print(f"핵심키워드 '{key}': {hits}회 (기준 3~4회)")
ok = not html and not links and not over and 3 <= hits <= 4
print("PASS" if ok else "FAIL")
