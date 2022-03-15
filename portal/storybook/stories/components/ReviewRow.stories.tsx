/* eslint-disable no-alert */
import AmendButton from "src/features/employer-review/AmendButton";
import React from "react";
import ReviewHeading from "src/components/ReviewHeading";
import ReviewRow from "src/components/ReviewRow";

export default {
  title: "Components/Review/ReviewRow",
  component: ReviewRow,
};

export const Default = () => (
  <ReviewRow
    level="3"
    label="Leave duration"
    editText="Edit"
    editHref="#duration"
  >
    04/12/2021 – 05/01/2021
    <br />
    Continuous
  </ReviewRow>
);

export const WithHeadings = () => (
  <React.Fragment>
    <ReviewHeading level="2" editText="Edit" editHref="#name">
      Verify your identity
    </ReviewHeading>

    <ReviewRow level="3" label="Name">
      Bud Baxter
    </ReviewRow>

    <ReviewHeading level="2" editText="Edit" editHref="#medical">
      Leave details
    </ReviewHeading>

    <ReviewRow level="3" label="Leave type">
      Medical
    </ReviewRow>
    <ReviewRow level="3" label="Leave duration">
      04/12/2021 – 05/01/2021
      <br />
      Continuous
    </ReviewRow>
  </React.Fragment>
);

export const WithAction = () => (
  <ReviewRow
    level="3"
    label="Employer notification date"
    action={
      <AmendButton
        onClick={() => alert("This function should open the Amendment Form!")}
      />
    }
  >
    01/01/2021
  </ReviewRow>
);
