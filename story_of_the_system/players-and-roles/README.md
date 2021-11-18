# Players and Roles

---
## Notes for Contributing

- Each player in the system is identified and their role in the claims process is described.

- The word "player" in this context refers to any entity or individual taking action in the claims process, from inception of a claim to payments complete.

- The player’s role is a description answering the question, “Why is this entity part of the process?”

    - A good way to answer this question is by asking what would be lacking, or what would happen to the system, if this player wasn’t part of it.

- The most important question to answer for these entities is “why this is here;” but for the sake of the information flow section, it will be useful to include each entity’s information needs, how it uses the information, and what information is produced/returned by it.

## Adding a new player: 
### If the player has an abbreviation (like DOR): 
> in the `players-and-roles` directory
```bash
$ python add_player.py "Example Player (EXP)"
```
### If not:
> in the `players-and-roles` directory
```bash
$ python add_player.py "Example Player"
```