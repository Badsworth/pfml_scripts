import React from "react";

/**
 * @deprecated
 */
export function TagD(props) {
  return (
    <span className={`${props.tag.split("-").join(" ").toLowerCase()} E2E-tag`}>
      {props.tag}
    </span>
  );
}

/**
 * @deprecated
 */
export function TagsFromArray(props) {
  if (typeof props.tags !== "object") {
    return <span />;
  }
  return props.tags
    .filter((tag) => tag != "Deploy")
    .map((tag) => <TagD tag={tag} />);
}

export function Tag({ tag, className }) {
  return (
    <span
      className={`${tag.split("-").join(" ").toLowerCase()} tag ${className}`}
    >
      {tag}
    </span>
  );
}

export function Tags({ tags, className }) {
  if (typeof tags === "string" && tags.length) {
    return <Tag tag={tags} />;
  }
  if (typeof tags !== "object") {
    return <span />;
  }
  return tags
    .filter((tag) => tag !== "Deploy")
    .map((tag) => <Tag tag={tag} className={className} />);
}
