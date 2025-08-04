render:
	uv run antlr4-parse SixNF.g4 parse -gui < example.6nf

python-gen: antlr4.jar
	java -jar antlr4.jar -Dlanguage=Python3 -listener SixNF.g4

antlr4.jar:
	curl -L --output antlr4.jar https://www.antlr.org/download/antlr-4.13.2-complete.jar

python-fmt:
	uv run ruff format
