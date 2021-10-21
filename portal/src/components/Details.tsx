import React from "react";

interface DetailsProps {
  label: string;
  children: React.ReactNode;
}

/**
 * A details element that expands and collapses.
 */
function Details(props: DetailsProps) {
  return (
    <details className="c-details">
      <summary className="margin-bottom-2 text-primary text-underline font-ui-xs">
        {props.label}
      </summary>
      <div className="margin-bottom-2">{props.children}</div>
    </details>
  );
}

export default Details;
