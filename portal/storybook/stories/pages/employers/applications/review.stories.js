import AppErrorInfo from "src/models/AppErrorInfo";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import { MockEmployerClaimBuilder } from "tests/test-utils";
import React from "react";
import { Review } from "src/pages/employers/applications/review";
import User from "src/models/User";

export default {
  title: "Pages/Employers/Applications/Review",
  component: Review,
  argTypes: {
    errorTypes: {
      control: {
        type: "check",
        options: [
          "Hours worked per week",
          "Employer benefit - benefit end date",
          "Previous leave - leave start date",
          "Previous leave - leave end date",
        ],
      },
    },
  },
};

export const Default = ({ errorTypes = [] }) => {
  const user = new User();
  const query = { absence_id: "mock-absence-id" };
  const appLogic = {
    appErrors: getAppErrorInfoCollection(errorTypes),
    employers: {
      claim: new MockEmployerClaimBuilder().completed().reviewable().create(),
      loadClaim: () => {},
      loadDocuments: () => {},
      submit: () => {},
    },
    setAppErrors: () => {},
  };
  return <Review appLogic={appLogic} query={query} user={user} />;
};

function getAppErrorInfoCollection(errorTypes = []) {
  const errors = [];
  if (errorTypes.includes("Hours worked per week")) {
    errors.push(
      new AppErrorInfo({
        message:
          "hours_worked_per_week must be greater than 0 and less than 168",
        type: "invalid_hours_worked_per_week",
        field: "hours_worked_per_week",
      })
    );
  }

  if (errorTypes.includes("Employer benefit - benefit end date")) {
    errors.push(
      new AppErrorInfo({
        message: "benefit_end_date cannot be earlier than benefit_start_date",
        type: "minimum",
        field: "employer_benefits[0].benefit_end_date",
      })
    );
  }

  if (errorTypes.includes("Previous leave - leave start date")) {
    errors.push(
      new AppErrorInfo({
        message: "Previous leaves cannot start before 2021",
        type: "invalid_previous_leave_start_date",
        field: "previous_leaves[0].leave_start_date",
      })
    );
  }

  if (errorTypes.includes("Previous leave - leave end date")) {
    errors.push(
      new AppErrorInfo({
        message: "leave_end_date cannot be earlier than leave_start_date",
        type: "minimum",
        field: "previous_leaves[0].leave_end_date",
      })
    );
  }

  return new AppErrorInfoCollection(errors);
}
