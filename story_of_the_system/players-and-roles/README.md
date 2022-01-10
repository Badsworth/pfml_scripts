# Players and Roles

### [Claimant](claimant/README.md)
### [Comptroller's Office](comptrollers-office/README.md)
### [Contact Center](contact-center/README.md)
### [DIA – Department of Industrial Accidents](department-of-industrial-accidents/README.md)
### [DUA – Department of Unemployment Assistance](department-of-unemployment-assistance/README.md)
### [Employer](employer/README.md)
### [FINEOS](fineos/README.md)
### [Leave Administrator](leave-administrator/README.md)
### [PUB – People's United Bank](peoples-united-bank/README.md)
### [RMV – Registry of Motor Vehicles](registry-of-motor-vehicles/README.md)

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