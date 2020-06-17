import React from "react";
import ReviewHeading from "./ReviewHeading";

export default {
  title: "Components/ReviewHeading",
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
