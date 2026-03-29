install:
	python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

generate:
	.venv/bin/python generate.py

clean:
	rm -rf output/
