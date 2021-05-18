import { ScenarioSpecification } from "../generation/Scenario";
import { map } from "streaming-iterables";
import { Readable } from "stream";
import stringify from "csv-stringify";
import { generators } from "../generation/documents";
import { formatISO } from "date-fns";
import multipipe from "multipipe";
import yaml from "js-yaml";

function describeClaimLeaveType(claimSpec: ScenarioSpecification["claim"]) {
  if (claimSpec.has_continuous_leave_periods) {
    return "Continuous";
  }
  if (claimSpec.has_intermittent_leave_periods) {
    return "Intermittent";
  }
  if (claimSpec.reduced_leave_spec) {
    return `Reduced (${claimSpec.reduced_leave_spec})`;
  }
  return "Continuous";
}

function describeClaimLeaveDates(claimSpec: ScenarioSpecification["claim"]) {
  if (claimSpec.leave_dates) {
    return claimSpec.leave_dates
      .map((date) => formatISO(date, { representation: "date" }))
      .join(" - ");
  }
  if (claimSpec.shortClaim) {
    return "Random (short leave)";
  }
  return "Random over next 60 days";
}

function describeCertificationDocs(spec: ScenarioSpecification["claim"]) {
  const matchingDocs = Object.keys(spec.docs ?? {}).filter((documentKey) => {
    const generator = generators[documentKey as keyof typeof generators];
    return (
      generator &&
      (generator.documentType === "State managed Paid Leave Confirmation" ||
        generator.documentType === "Child bonding evidence form" ||
        generator.documentType === "Own serious health condition form" ||
        generator.documentType === "Care for a family member form")
    );
  });
  if (!matchingDocs) {
    return "N/A";
  }
  return matchingDocs
    .map((key) => {
      const config = spec.docs?.[key as keyof typeof generators];
      const invalid = config && "invalid" in config && config.invalid;
      return `${key}${invalid ? " (invalid)" : ""}`;
    })
    .join(", ");
}

function describeIDProofDocs(spec: ScenarioSpecification["claim"]) {
  const matchingDocs = Object.keys(spec.docs ?? {}).filter((documentKey) => {
    const generator = generators[documentKey as keyof typeof generators];
    return generator && generator.documentType === "Identification Proof";
  });
  if (!matchingDocs) {
    return "N/A";
  }
  return matchingDocs
    .map((key) => {
      const config = spec.docs?.[key as keyof typeof generators];
      const invalid = config && "invalid" in config && config.invalid;
      return `${key}${invalid ? " (invalid)" : ""}`;
    })
    .join(", ");
}

function describeEmployerResponse(spec: ScenarioSpecification["claim"]) {
  return spec.employerResponse ? yaml.dump(spec.employerResponse) : "__none__";
}

function describeAddress(spec: ScenarioSpecification["claim"]) {
  if (spec.address) {
    return yaml.dump(spec.address);
  }
  return "__random__";
}

function describePaymentDetails(spec: ScenarioSpecification["claim"]): string {
  if (spec.payment) {
    return yaml.dump(spec.payment);
  }
  return "__random__";
}

type ScenarioDescription = Record<
  keyof typeof columns,
  string | number | null | undefined
>;

function describeScenario(
  scenario: ScenarioSpecification
): ScenarioDescription {
  return {
    name: scenario.claim.label,
    employeeWages: scenario.employee.wages ?? "Eligible",
    claimReason: scenario.claim.reason,
    claimReasonQualifier: scenario.claim.reason_qualifier ?? "N/A",
    claimLeaveDates: describeClaimLeaveDates(scenario.claim),
    claimLeaveType: describeClaimLeaveType(scenario.claim),
    claimWorkPattern: scenario.claim.work_pattern_spec ?? "standard",
    claimPregnantOrBirth: scenario.claim.pregnant_or_recent_birth
      ? "Yes"
      : "N/A",
    claimAddress: describeAddress(scenario.claim),
    paymentDetails: describePaymentDetails(scenario.claim),
    documentCertification: describeCertificationDocs(scenario.claim),
    documentIDProof: describeIDProofDocs(scenario.claim),
    employerResponse: describeEmployerResponse(scenario.claim),
    employeeMetadata: yaml.dump(scenario.employee.metadata),
    claimMetadata: yaml.dump(scenario.claim.metadata),
  };
}

const columns = {
  name: "Scenario",
  employeeWages: "Employee Wages",
  claimReason: "Reason",
  claimReasonQualifier: "Reason Qualifier",
  claimLeaveDates: "Leave Dates",
  claimLeaveType: "Leave Type",
  claimWorkPattern: "Work Pattern",
  claimPregnantOrBirth: "Pregnant/Birth",
  claimAddress: "Mailing/Residential Address",
  paymentDetails: "Payment Details",
  documentCertification: "Certification Document",
  documentIDProof: "ID Proof Document",
  employerResponse: "Employer Response",
  employeeMetadata: "Employee Metadata",
  claimMetadata: "Claim Metadata",
};

const describeScenarios = map(describeScenario);

export default (scenarios: ScenarioSpecification[]): NodeJS.ReadableStream =>
  multipipe(
    Readable.from(describeScenarios(scenarios)),
    stringify({
      header: true,
      columns,
    })
  );
