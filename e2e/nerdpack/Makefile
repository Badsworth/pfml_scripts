info:
	nr1 nerdpack:info

local:
	npm start

publish: version/bump publish/dev

publish/dev:
	nr1 nerdpack:publish --tag="DEV"

promote:
	nr1 nerdpack:tag

version/bump:
	npm version patch

