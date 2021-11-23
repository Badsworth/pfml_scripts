import re
from sys import argv
from pathlib import Path

full_tool_name = " ".join(argv[1:])
has_abbreviation = False
abbreviation = ""
separator = "---\n"

if re.search(r"\([A-Z]+\)", full_tool_name):
    abbreviation = re.sub("^.*?\(([A-Z]+)\)", r"\1", full_tool_name)
    has_abbreviation = True

tool_name = re.sub("(^[A-Za-z0-9 ']+) \([A-Z]+\)", r"\1", full_tool_name)
directory_name = "-".join(tool_name.replace("'", "").lower().split(" "))
readme_heading = f"# {full_tool_name}\n\n"
if has_abbreviation:
    hyperlink = f"### [{abbreviation} – {tool_name}]({directory_name}/README.md)"
else:
    hyperlink = f"### [{tool_name}]({directory_name}/README.md)"

# -------------------------------------------------------------------------------
#                     Add tool to list of tools
# -------------------------------------------------------------------------------

with open("README.md", "r") as file:
    lines = file.readlines()

# Insert new tool and re-sort list
lines.insert(2, f"{hyperlink}\n")
tool_links = list(filter(lambda a: a != "\n", lines[1 : lines.index(separator)]))
tool_links.sort()

# Build new README
heading = "# Tools\n\n"
tool_links = "".join(tool_links)
notes = "".join(lines[lines.index(separator) :])
new_readme = f"{heading}{tool_links}\n{notes}"


with open("README.md", "w") as file:
    file.write(new_readme)

# -------------------------------------------------------------------------------
#                Create directory and README for new tool
# -------------------------------------------------------------------------------

new_dir = Path(directory_name)

try:
    Path.mkdir(new_dir)
except OSError as error:
    print(error)

with open("template.md", "r") as file:
    templt = file.read()

if has_abbreviation:
    pre_template = re.sub("Tool X ", f"{full_tool_name}\n", templt)
    new_template = re.sub("Tool Xa", abbreviation, pre_template)
else:
    new_template = re.sub(r"Tool X |Tool Xa", f"{full_tool_name}\n", templt)


with open(f"{directory_name}/README.md", "w") as file:
    file.write(new_template)
