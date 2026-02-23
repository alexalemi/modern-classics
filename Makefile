.PHONY: deploy

deploy:
	rsync -avz --delete site/ nubo:~/static/modern-classics/
