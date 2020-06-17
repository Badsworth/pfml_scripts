import React from "react";
import ReviewHeading from "./ReviewHeading";
import ReviewRow from "./ReviewRow";

export default {
  title: "Components/ReviewRow",
  component: ReviewRow,
};

export const Default = () => (
  <ReviewRow label="Leave duration" editText="Edit" editHref="#duration">
    04/12/2021 – 05/01/2021
    <br />
    Continuous
  </ReviewRow>
);

export const WithHeadings = () => (
  <React.Fragment>
    <ReviewHeading editText="Edit" editHref="#name">
      Verify your identity
    </ReviewHeading>

    <ReviewRow label="Name">Bud Baxter</ReviewRow>

    <ReviewHeading editText="Edit" editHref="#medical">
      Leave details
    </ReviewHeading>

    <ReviewRow label="Leave type">Medical</ReviewRow>
    <ReviewRow label="Leave duration">
      04/12/2021 – 05/01/2021
      <br />
      Continuous
    </ReviewRow>
  </React.Fragment>
);
