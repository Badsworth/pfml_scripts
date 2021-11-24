import re
from sys import argv
from pathlib import Path

full_player_name = " ".join(argv[1:])
has_abbreviation = False
abbreviation = ""
separator = "---\n"

if re.search(r"\([A-Z]+\)", full_player_name):
    abbreviation = re.sub("^.*?\(([A-Z]+)\)", r"\1", full_player_name)
    has_abbreviation = True

player_name = re.sub("(^[A-Za-z0-9 ']+) \([A-Z]+\)", r"\1", full_player_name)
directory_name = "-".join(player_name.replace("'", "").lower().split(" "))
readme_heading = f"# {full_player_name}\n\n"
if has_abbreviation:
    hyperlink = f"### [{abbreviation} – {player_name}]({directory_name}/README.md)"
else:
    hyperlink = f"### [{player_name}]({directory_name}/README.md)"

# -------------------------------------------------------------------------------
#                     Add player to list of players
# -------------------------------------------------------------------------------

with open("README.md", "r") as file:
    lines = file.readlines()

# Insert new player and re-sort list
lines.insert(2, f"{hyperlink}\n")
player_links = list(filter(lambda a: a != "\n", lines[1 : lines.index(separator)]))
player_links.sort()

# Build new README
heading = "# Players and Roles\n\n"
player_links = "".join(player_links)
notes = "".join(lines[lines.index(separator) :])
new_readme = f"{heading}{player_links}\n{notes}"


with open("README.md", "w") as file:
    file.write(new_readme)

# -------------------------------------------------------------------------------
#                Create directory and README for new player
# -------------------------------------------------------------------------------

new_dir = Path(directory_name)

try:
    Path.mkdir(new_dir)
except OSError as error:
    print(error)

with open("template.md", "r") as file:
    templt = file.read()

if has_abbreviation:
    pre_template = re.sub("Entity 𝑋 ", f"{full_player_name}\n", templt)
    new_template = re.sub("Entity 𝑋a", abbreviation, pre_template)
else:
    new_template = re.sub(r"Entity 𝑋 |Entity 𝑋a", f"{full_player_name}\n", templt)


with open(f"{directory_name}/README.md", "w") as file:
    file.write(new_template)
