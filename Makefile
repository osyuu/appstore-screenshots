install:
	python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

generate:
	@echo "Usage: make generate APP=YourApp [DEVICE=iphone|ipad|all]"
	@test -n "$(APP)" || (echo "Error: APP is required" && exit 1)
	.venv/bin/python generate.py --app $(APP) --device $(or $(DEVICE),all)

clean:
	rm -rf output/
