import React, { useEffect, useState } from "react";
import Eligible from "../../components/Eligible";
import Exemption from "../../components/Exemption";
import Ineligible from "../../components/Ineligible";
import RecordNotFound from "../../components/RecordNotFound";
import Spinner from "../../components/Spinner";
import { useRouter } from "next/router";
import { useTranslation } from "react-i18next";

// TODO replace with request to eligibility endpoint
const mockEligibilityRequest = eligibility => eligibility;

const Result = () => {
  const router = useRouter();
  const { t } = useTranslation();
  // eligibility parameter for mocking different responses
  // oneof "eligible", "ineligible", "exempt", "notfound"
  const { employeeId, mockEligibility } = router.query;
  const [eligibility, setEligibility] = useState();

  useEffect(() => {
    setEligibility(mockEligibilityRequest(mockEligibility));
  }, [mockEligibility]);

  if (!eligibility) {
    return (
      <div className="margin-top-8 text-center">
        <Spinner aria-valuetext={t("components.spinner.label")} />
      </div>
    );
  }

  switch (eligibility) {
    case "exempt":
      return <Exemption />;
    case "eligible":
      return <Eligible employeeId={employeeId} />;
    case "ineligible":
      return <Ineligible employeeId={employeeId} />;
    case "notfound":
      return <RecordNotFound />;
    default:
      // TODO this should return either an error message or a 404
      return null;
  }
};

export default Result;
