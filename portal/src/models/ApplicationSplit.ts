import BenefitYear from "./BenefitYear";
import { ISO8601Timestamp } from "types/common";
interface StartEndDates {
  start_date: ISO8601Timestamp;
  end_date: ISO8601Timestamp;
}

interface ApplicationSplit {
  crossed_benefit_year: BenefitYear;
  application_dates_in_benefit_year: StartEndDates;
  application_dates_outside_benefit_year: StartEndDates;
  application_outside_benefit_year_submittable_on: ISO8601Timestamp;
}

export default ApplicationSplit;
