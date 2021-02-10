# Used by GitHub Actions during the GH Pages Deploy workflow to ensure
# all links to code files are hardcoded with the repository URL.
#
# example:
#   ../../api/README.md --> https://github.com/EOLWD/pfml/tree/master/api/README.md
#
import fileinput
import glob


def replace_paths():
    for filepath in glob.iglob('./docs/**/*.md', recursive=True):
        # Determine how many relative directories back there will be based on
        # how many folders deep we are in the docs folder.
        #
        # e.g. if the source file is /docs/portal/deployment.md,
        #      all file relative paths should be ../../ to refer to the repo root.
        #
        nesting_count = filepath.count("/") - 1
        prefix = ''.join('../' * nesting_count)

        # Open the source file and replace the relative and absolute root prefixes with hardcoded links to Github.
        #
        with fileinput.FileInput(filepath, inplace=True) as f:
            for line in f:
                print(line\
                    .replace(f"]({prefix}", "](https://github.com/EOLWD/pfml/tree/master/")\
                    .replace(f"](/", "](https://github.com/EOLWD/pfml/tree/master/"), end='')


replace_paths()
