import ChangeRequest, { ChangeRequestType } from "src/models/ChangeRequest";
import { Props, ValuesOf } from "types/common";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import React from "react";
import { Review } from "src/pages/applications/modify/review";
import User from "src/models/User";
import createMockClaimDetail from "lib/mock-helpers/createMockClaimDetail";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: `Pages/Applications/Modify/Review`,
  component: Review,

  args: {
    "Change request type": "Modification",
    "Uploaded proof of birth": false,
    "Pending claim": false,
    "End leave early": false,
  },
  argTypes: {
    "Change request type": {
      control: {
        type: "radio",
        options: Object.values(ChangeRequestType),
      },
    },
    "Uploaded proof of birth": {
      control: {
        type: "boolean",
      },
    },
    "Pending claim": {
      control: {
        type: "boolean",
      },
    },
    "End leave early": {
      control: {
        type: "boolean",
      },
    },
  },
};

export const Default = (
  args: Props<typeof Review> & {
    "Change request type": ValuesOf<typeof ChangeRequestType>;
    "Uploaded proof of birth": false;
    "Pending claim": false;
    "End leave early": false;
  }
) => {
  const claimDetail = createMockClaimDetail({
    leaveScenario: "Medical (pregnancy)",
    requestDecision: args["Pending claim"] ? "Pending" : "Approved",
  });

  claimDetail.absence_periods = [
    {
      ...claimDetail.absence_periods[0],
      absence_period_end_date: "2022-03-01",
      absence_period_start_date: "2022-01-01",
    },
  ];

  const changeRequest = new ChangeRequest({
    change_request_type: args["Change request type"],
    fineos_absence_id: "absence-id",
    change_request_id: "change-request-id",
    documents_submitted_at: args["Uploaded proof of birth"]
      ? "2022-01-01"
      : null,
    start_date: claimDetail.absence_periods[0].absence_period_start_date,
    end_date: args["End leave early"] ? "2022-02-01" : "2022-03-30",
  });

  const appLogic = useMockableAppLogic({
    claims: {
      claimDetail,
      isLoadingClaimDetail: false,
    },
    changeRequests: {
      changeRequests: new ApiResourceCollection("change_request_id", [
        changeRequest,
      ]),
    },
  });

  return (
    <Review
      change_requests={
        new ApiResourceCollection<ChangeRequest>("change_request_id", [])
      }
      claim_detail={claimDetail}
      change_request={changeRequest}
      appLogic={appLogic}
      user={new User({})}
    />
  );
};
