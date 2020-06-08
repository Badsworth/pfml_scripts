import Heading from "./Heading";
import React from "react";
import ReviewRow from "./ReviewRow";

export default {
  title: "Components/ReviewRow",
  component: ReviewRow,
};

export const Default = () => (
  <ReviewRow heading="Leave duration" editText="Edit" editHref="#duration">
    04/12/2021 – 05/01/2021
    <br />
    Continuous
  </ReviewRow>
);

export const WithSurroundingMarkup = () => (
  <React.Fragment>
    <Heading level="2">Verify your identity</Heading>
    <ReviewRow heading="Name" editText="Edit" editHref="#name">
      Bud Baxter
    </ReviewRow>

    <Heading level="2">Leave details</Heading>
    <ReviewRow heading="Leave type" editText="Edit" editHref="#medical">
      Medical
    </ReviewRow>
    <ReviewRow heading="Leave duration" editText="Edit" editHref="#duration">
      04/12/2021 – 05/01/2021
      <br />
      Continuous
    </ReviewRow>
  </React.Fragment>
);
