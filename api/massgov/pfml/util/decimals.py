from decimal import Decimal

TWOPLACES = Decimal(10) ** -2


def round_nearest_hundredth(decimal: Decimal) -> Decimal:
    return decimal.quantize(TWOPLACES)
