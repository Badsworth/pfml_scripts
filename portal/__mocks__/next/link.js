import React from "react";

// Resolves error: Cannot read property 'prefetch'
// https://github.com/vercel/next.js/issues/16864#issuecomment-702069418
export default function Link({ children, ...props }) {
  return React.cloneElement(children, props);
}
