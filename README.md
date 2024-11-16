# tf-flask

## Installation

	7zz x tf-flask.7z #(or git clone ...)
	cd tf-flask
	python3 -m venv .venv
	. .venv/bin/activate
	pip install -r requirements.txt
	#test:
	flask run
	#production run:
	gunicorn -b localhost:5000 app:app
	# try calling from outside of venv:
	deactivate
	.venv/bin/gunicorn -b localhost:5000 app:app


If all goes well, create, enable, and start systemd service. (google it)
