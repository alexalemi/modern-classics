.PHONY: deploy

deploy: feeds
	rsync -avz --delete site/ nubo:~/static/modern-classics/

.PHONY: feeds
feeds:
	python3 build_feeds.py

.PHONY: about
about:
	python3 build_about.py

.PHONY: ebooks
ebooks:
	python3 -c "import json; [__import__('subprocess').run(['python3','build_ebook.py',b],check=False) for b in json.load(open('ebook_meta.json'))]"
