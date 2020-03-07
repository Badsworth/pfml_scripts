import Exemption from "../../components/Exemption";
import React from "react";

const Result = () => {
  const displayResults = () => {
    // TODO Display other results.
    return <Exemption />;
  };

  return <React.Fragment>{displayResults()}</React.Fragment>;
};

export default Result;
