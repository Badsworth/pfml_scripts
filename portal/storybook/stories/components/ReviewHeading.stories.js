import React from "react";
import ReviewHeading from "src/components/ReviewHeading";

export default {
  title: "Components/Review/ReviewHeading",
  component: ReviewHeading,
};

export const Default = () => (
  <ReviewHeading editText="Edit" editHref="#duration">
    Who is taking leave?
  </ReviewHeading>
);

export const NoEditLink = () => (
  <ReviewHeading>Who is taking leave?</ReviewHeading>
);
