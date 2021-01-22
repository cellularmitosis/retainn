default: test serve3

test: test3 test2

test3:
	python3 tests.py

test2:
	python2 tests.py

serve3: db
	python3 bin/retainn serve

serve2: db
	python2 bin/retainn serve

#run-wsgi: db
#	mod_wsgi-express start-server retainn_webapp.wsgi

deps-mac:
	brew install python
#	pip3 install flask mod_wsgi

db: ~/.retainn/db.sqlite3

~/.retainn/db.sqlite3: lib/retainn/sql/schema.sql
	cat lib/retainn/sql/schema.sql | sqlite3 ~/.retainn/db.sqlite3

import: db
	./bin/retainn import 'https://gist.github.com/cellularmitosis/fe539a6529d3787d94517f94def1bc4d'
	./bin/retainn import 'https://gist.github.com/cellularmitosis/1890a73accb817a2491dd8d335156512'
	./bin/retainn import 'https://gist.github.com/cellularmitosis/0f8fa92144f4821c113b143e7a80af00'

clean:
	rm -f lib/retainn/*.pyc
	rm -rf lib/retainn/__pycache__

.PHONY: default serve serve2 serve3 run-wsgi test test2 test3 deps-mac db clean
