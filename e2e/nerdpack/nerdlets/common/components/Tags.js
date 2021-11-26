import React from "react";

export function Tag(props) {
  return (
    <span className={`${props.tag.split("-").join(" ").toLowerCase()} E2E-tag`}>
      {props.tag}
    </span>
  );
}

export function TagsFromArray(props) {
  if (typeof props.tags !== "object") {
    return <span />;
  }
  return props.tags.map((tag) => <Tag tag={tag} />);
}
