import Heading from "./core/Heading";
import Link from "next/link";
import React from "react";

interface ReviewHeadingProps {
  children: string;
  editHref?: string;
  editText?: React.ReactNode;
  level: "2" | "3" | "4" | "5" | "6";
}

/**
 * Heading for a group of ReviewRow components
 */
const ReviewHeading = (props: ReviewHeadingProps) => {
  return (
    <div className="display-flex flex-align-end margin-top-6 margin-bottom-3">
      <Heading
        className="flex-fill margin-right-1"
        level={props.level}
        size="2"
      >
        {props.children}
      </Heading>
      {props.editHref && (
        <Link href={props.editHref}>
          <a
            className="usa-link margin-0"
            aria-label={`${props.editText}: ${props.children}`}
          >
            {props.editText}
          </a>
        </Link>
      )}
    </div>
  );
};

export default ReviewHeading;
