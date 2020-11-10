#
# Eligibility - benefit calculations.
#
# See https://lwd.atlassian.net/wiki/spaces/DD/pages/341049523/Benefit+Calculation
#

import datetime
import decimal


def calculate_weekly_benefit_amount(
    individual_average_weekly_wage: int,
    state_average_weekly_wage: decimal.Decimal,
    effective_date: datetime.date,
) -> decimal.Decimal:
    # Terminology note: aww = average weekly wage

    individual_aww = decimal.Decimal(individual_average_weekly_wage)

    if effective_date.year == 2021:
        # Maximum benefit for the 1st yr of the program is $850
        maximum_benefit = decimal.Decimal(850)
    else:
        maximum_benefit = state_average_weekly_wage * decimal.Decimal("0.64")

    half_state_aww = state_average_weekly_wage * decimal.Decimal("0.5")

    # Split the individual aww into the portion below 50% of the state aww and the portion above
    # 50% of the state aww. These two lines handle both cases:
    # - when the individual aww is below 50% state aww, portion below is the entire wage, and
    #   portion above is 0
    # - otherwise the individual aww is split into 50% state aww and the rest
    portion_below_half_state_aww = min(individual_aww, half_state_aww)
    portion_above_half_state_aww = individual_aww - portion_below_half_state_aww

    # 80% wage replacement for the portion below
    #                    and
    # 50% wage replacement for the portion above.
    benefit_amount = (
        decimal.Decimal("0.8") * portion_below_half_state_aww
        + decimal.Decimal("0.5") * portion_above_half_state_aww
    )

    if maximum_benefit < benefit_amount:
        benefit_amount = maximum_benefit

    return benefit_amount
