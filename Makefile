PROJECT = kyotocabinet
VERSION = $(shell cat VERSION)
BUILD_NUM ?= 0

PYTHON = python3
RUNENV = LD_LIBRARY_PATH=.:/lib:/usr/lib:/usr/local/lib:$(HOME)/lib

install: clean
	@poetry install

update: clean
	@poetry update

clean :
	rm -rf casket casket* *.kcss *.so *.pyc build dist hoge moge tako ika
	rm -rf */__pycache__
	rm -rf */*.pyc

hooks:
	pre-commit install --hook-type pre-commit --hook-type pre-push

pep8 flake:
	@poetry run flakeheaven lint $(PROJECT)

test: build
	@poetry run pytest tests/

static-checks: pep8

build:
	@poetry version "${VERSION}.${BUILD_NUM}"
	@poetry build -f wheel -n

publish:
	@poetry config repositories.bcd ${PYPI_URL}
	@poetry publish -r bcd -u ${PYPI_USERNAME} -p ${PYPI_PASSWORD}

check: build
	$(MAKE) DBNAME=":" RNUM="10000" check-each
	$(MAKE) DBNAME="*" RNUM="10000" check-each
	$(MAKE) DBNAME="%" RNUM="10000" check-each
	$(MAKE) DBNAME="casket.kch" RNUM="10000" check-each
	$(MAKE) DBNAME="casket.kct" RNUM="10000" check-each
	$(MAKE) DBNAME="casket.kcd" RNUM="1000" check-each
	$(MAKE) DBNAME="casket.kcf" RNUM="10000" check-each
	@printf '\n'
	@printf '#================================================================\n'
	@printf '# Checking completed.\n'
	@printf '#================================================================\n'

check-each:
	rm -rf casket*
	$(RUNENV) $(PYTHON) kctest.py order "$(DBNAME)" "$(RNUM)"
	$(RUNENV) $(PYTHON) kctest.py order -rnd "$(DBNAME)" "$(RNUM)"
	$(RUNENV) $(PYTHON) kctest.py order -etc "$(DBNAME)" "$(RNUM)"
	$(RUNENV) $(PYTHON) kctest.py order -rnd -etc "$(DBNAME)" "$(RNUM)"
	$(RUNENV) $(PYTHON) kctest.py order -th 4 "$(DBNAME)" "$(RNUM)"
	$(RUNENV) $(PYTHON) kctest.py order -th 4 -rnd "$(DBNAME)" "$(RNUM)"
	$(RUNENV) $(PYTHON) kctest.py order -th 4 -etc "$(DBNAME)" "$(RNUM)"
	$(RUNENV) $(PYTHON) kctest.py order -th 4 -rnd -etc "$(DBNAME)" "$(RNUM)"
	$(RUNENV) $(PYTHON) kctest.py order -cc -th 4 -rnd -etc "$(DBNAME)" "$(RNUM)"
	$(RUNENV) $(PYTHON) kctest.py wicked "$(DBNAME)" "$(RNUM)"
	$(RUNENV) $(PYTHON) kctest.py wicked -it 4 "$(DBNAME)" "$(RNUM)"
	$(RUNENV) $(PYTHON) kctest.py wicked -th 4 "$(DBNAME)" "$(RNUM)"
	$(RUNENV) $(PYTHON) kctest.py wicked -th 4 -it 4 "$(DBNAME)" "$(RNUM)"
	$(RUNENV) $(PYTHON) kctest.py wicked -cc -th 4 -it 4 "$(DBNAME)" "$(RNUM)"
	$(RUNENV) $(PYTHON) kctest.py misc "$(DBNAME)"
	rm -rf casket*

check-forever:
	while true ; \
	  do \
	    $(MAKE) check || break ; \
	  done

doc: docclean
	cp -f kyotocabinet-doc.py kyotocabinet.py
	-mv -f kyotocabinet kyotocabinet-mod || true
	-epydoc --name kyotocabinet --no-private --no-sourcecode -o doc -q kyotocabinet.py
	-mv -f kyotocabinet-mod kyotocabinet || true
	rm -f kyotocabinet.py

docclean:
	rm -rf doc

.PHONY: install update clean pep8 hooks test static-checks build publish \
	check check-each check-forever doc docclean
