import React from "react";

/**
 * The page a user is redirected to by default after
 * successfully authenticating.
 * @returns {React.Component}
 */
const Index = () => (
  <React.Fragment>
    <h2 className="font-heading-2xl">Dashboard</h2>
    <div className="usa-prose">
      <p>Thanks for logging in.</p>
    </div>
  </React.Fragment>
);

export default Index;
