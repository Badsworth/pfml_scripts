"""
The function checks correctness of a routing number using the Checksum algorithm.
Checksum algorithm: http://en.wikipedia.org/wiki/Routing_transit_number#Check_digit
"""


def validate_routing_number(routing_number: str) -> bool:
    if len(routing_number) != 9:
        return False

    n = 0
    for i in range(0, len(routing_number), 3):
        n += int(routing_number[i]) * 3
        n += int(routing_number[i + 1]) * 7
        n += int(routing_number[i + 2])

    if n != 0 and n % 10 == 0:
        return True
    else:
        return False
