import React from "react";
import ReviewHeading from "src/components/ReviewHeading";

export default {
  title: "Components/Review/ReviewHeading",
  component: ReviewHeading,
};

export const Default = () => (
  <ReviewHeading level="2" editText="Edit" editHref="#duration">
    Who is taking leave?
  </ReviewHeading>
);

export const NoEditLink = () => (
  <ReviewHeading level="2">Who is taking leave?</ReviewHeading>
);
