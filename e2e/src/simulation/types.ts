// @todo: This type is incomplete. Fill it in more later on, or extract from OpenAPI
export interface PortalApplicationSubmission {
  application_id?: string;
  date_of_birth: string;
  employment_status: string;
  first_name: string;
  last_name: string;
  leave_details: {
    continuous_leave_periods: PortalContinuousLeavePeriod[];
    employer_notification_date: string;
    employer_notified: boolean;
    intermittent_leave_periods: PortalIntermittentLeavePeriod[];
    reason: string;
    reduced_schedule_leave_periods: [];
  };
  payment_preferences: [];
  status: string;
  tax_identifier_last4: string;
}
interface PortalContinuousLeavePeriod {
  start_date: string;
  end_date: string;
  is_estimated: boolean;
}
interface PortalIntermittentLeavePeriod {
  is_estimated: boolean;
}
