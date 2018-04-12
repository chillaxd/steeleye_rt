#
# Makefile to build Lambda zip file
#

lambda:
	@sh package.sh steeleye

build: lambda

.PHONY: lambda build
