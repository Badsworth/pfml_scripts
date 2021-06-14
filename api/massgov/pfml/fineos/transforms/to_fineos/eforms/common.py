from massgov.pfml.api.models.applications.common import OtherIncome
from massgov.pfml.api.models.common import ConcurrentLeave, EmployerBenefit, PreviousLeave


class IntermediaryConcurrentLeave:
    def __init__(self, leave: ConcurrentLeave):
        self.leave_start_date = leave.leave_start_date
        self.leave_end_date = leave.leave_end_date
        self.is_for_current_employer = "Yes" if leave.is_for_current_employer else "No"
        self.accrued_paid_leave = "Yes"


class IntermediaryEmployerBenefit:
    def __init__(self, benefit: EmployerBenefit):
        self.benefit_start_date = benefit.benefit_start_date
        self.benefit_end_date = benefit.benefit_end_date
        self.benefit_amount_dollars = benefit.benefit_amount_dollars
        self.benefit_amount_frequency = benefit.benefit_amount_frequency
        self.benefit_type = benefit.benefit_type
        self.is_full_salary_continuous = "Yes" if benefit.is_full_salary_continuous else "No"
        self.receive_wage_replacement = "Yes"


class IntermediaryOtherIncome:
    def __init__(self, income: OtherIncome):
        self.income_type = income.income_type
        self.income_start_date = income.income_start_date
        self.income_end_date = income.income_end_date
        self.income_amount_dollars = income.income_amount_dollars
        self.income_amount_frequency = income.income_amount_frequency
        self.receive_wage_replacement = "Yes"


class IntermediaryPreviousLeave:
    def __init__(self, leave: PreviousLeave):
        self.leave_start_date = leave.leave_start_date
        self.leave_end_date = leave.leave_end_date
        self.is_for_current_employer = "Yes" if leave.is_for_current_employer else "No"
        self.is_for_same_reason = "Yes" if leave.type == "same_reason" else "No"
        self.leave_reason = leave.leave_reason
        if leave.worked_per_week_minutes:
            self.worked_per_week_hours = int(leave.worked_per_week_minutes / 60)
            self.worked_per_week_minutes = format(leave.worked_per_week_minutes % 60, "02d")
        else:
            self.worked_per_week_hours = 0
            self.worked_per_week_minutes = "Please Select"
        if leave.leave_minutes:
            self.leave_hours = int(leave.leave_minutes / 60)
            self.leave_minutes = format(leave.leave_minutes % 60, "02d")
        else:
            self.leave_hours = 0
            self.leave_minutes = "Please Select"
        self.applies = "Yes"
