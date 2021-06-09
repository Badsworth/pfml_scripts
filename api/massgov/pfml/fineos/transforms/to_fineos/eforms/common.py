from massgov.pfml.api.models.common import EmployerBenefit


class IntermediaryEmployerBenefit:
    def __init__(self, benefit: EmployerBenefit):
        self.benefit_start_date = benefit.benefit_start_date
        self.benefit_end_date = benefit.benefit_end_date
        self.benefit_amount_dollars = benefit.benefit_amount_dollars
        self.benefit_amount_frequency = benefit.benefit_amount_frequency
        self.benefit_type = benefit.benefit_type
        self.is_full_salary_continuous = "Yes" if benefit.is_full_salary_continuous else "No"
