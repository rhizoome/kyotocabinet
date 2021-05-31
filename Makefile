# Makefile for Kyoto Cabinet for Python


PACKAGE = kyotocabinet-python
VERSION = 1.22
PACKAGEDIR = $(PACKAGE)-$(VERSION)
PACKAGETGZ = $(PACKAGE)-$(VERSION).tar.gz

PYTHON = python3
PIP = pip
RUNENV = LD_LIBRARY_PATH=.:/lib:/usr/lib:/usr/local/lib:$(HOME)/lib


all :
	$(PYTHON) setup.py build
	cp -f build/*/*.so .
	@printf '\n'
	@printf '#================================================================\n'
	@printf '# Ready to install.\n'
	@printf '#================================================================\n'


clean :
	rm -rf casket casket* *~ *.tmp *.kcss *.so *.pyc build hoge moge tako ika


install :
	$(PYTHON) setup.py install
	@printf '\n'
	@printf '#================================================================\n'
	@printf '# Thanks for using Kyoto Cabinet for Python.\n'
	@printf '#================================================================\n'


uninstall :
	$(PYTHON) setup.py install --record files.tmp
	xargs rm -f < files.tmp


dist :
	$(MAKE) clean
	cd .. && tar cvf - $(PACKAGEDIR) | gzip -c > $(PACKAGETGZ)


check :
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


check-each :
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


check-forever :
	while true ; \
	  do \
	    $(MAKE) check || break ; \
	  done


doc :
	$(MAKE) docclean
	cp -f kyotocabinet-doc.py kyotocabinet.py
	-[ -f kyotocabinet.so ] && mv -f kyotocabinet.so kyotocabinet-mod.so || true
	-epydoc --name kyotocabinet --no-private --no-sourcecode -o doc -q kyotocabinet.py
	-[ -f kyotocabinet-mod.so ] && mv -f kyotocabinet-mod.so kyotocabinet.so || true
	rm -f kyotocabinet.py


docclean :
	rm -rf doc


build :
	$(PIP) install wheel
	BUILD_NUM=${BUILD_NUM} $(PYTHON) setup.py build bdist_wheel


publish :
	$(PIP) install twine
	twine upload -u ${PYPI_USERNAME} -p ${PYPI_PASSWORD} --repository-url ${PYPI_URL} dist/*


.PHONY: all clean install check doc build publish



# END OF FILE
