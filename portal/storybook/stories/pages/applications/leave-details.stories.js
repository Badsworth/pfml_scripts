import LeaveDetails from "src/pages/applications/leave-details.js";
import React from "react";

export default {
  title: "Pages/Applications/LeaveDetails",
  component: LeaveDetails,
};

// TODO(CP-2482): replace with AbsencePeriodModel
export const Default = () => (
  <LeaveDetails
    absenceDetails={{
      medical: [
        {
          period_type: "Reduced",
          absence_period_start_date: "2021-06-01",
          absence_period_end_date: "2021-06-08",
          request_decision: "Approved",
          fineos_leave_request_id: "PL-14432-0000002026",
        },
        {
          period_type: "Continuous",
          absence_period_start_date: "2021-07-01",
          absence_period_end_date: "2021-07-08",
          request_decision: "Pending",
          fineos_leave_request_id: "PL-14432-0000002326",
        },
      ],
      bonding: [
        {
          period_type: "Reduced",
          absence_period_start_date: "2021-08-01",
          absence_period_end_date: "2021-08-08",
          request_decision: "Denied",
          fineos_leave_request_id: "PL-14434-0000002026",
        },
        {
          period_type: "Continuous",
          absence_period_start_date: "2021-08-01",
          absence_period_end_date: "2021-08-08",
          request_decision: "Withdrawn",
          fineos_leave_request_id: "PL-14434-0000002326",
        },
      ],
    }}
  />
);
