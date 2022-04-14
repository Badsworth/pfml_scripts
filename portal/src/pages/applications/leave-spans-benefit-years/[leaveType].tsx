import { LeaveSpansBenefitYearInterstitial } from "src/features/benefits-applications/LeaveSpansBenefitYearsInterstitial";
import withBenefitsApplication from "src/hoc/withBenefitsApplication";

export default withBenefitsApplication(LeaveSpansBenefitYearInterstitial);

/* eslint-disable require-await */
export async function getStaticPaths() {
  return {
    paths: [
      { params: { leaveType: "continuous" } },
      { params: { leaveType: "intermittent" } },
      { params: { leaveType: "reduced" } },
    ],
    fallback: false,
  };
}

export async function getStaticProps() {
  return {
    props: {},
  };
}
