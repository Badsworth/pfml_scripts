type DateObj = { month: number; day: number; year: number };
export type Application = {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  dob: DateObj;
  massId?: string;
  idVerification?: { front: string; back: string };
  ssn: string;
  claim: Claim;
  employer: Employer;
  otherBenefits: OtherBenefits;
  paymentInfo: PaymentInfo;
};

export type Claim = MedicalClaim | FamilyClaim;
export type MedicalLeave = {
  type: "continuous" | "reduced" | "intermittent";
  typeBasedDetails: {
    weeks?: number;
    hoursPerWeek?: number;
    frequencyIntervalBasis?: "weeks" | "months" | "every6Months";
    frequency?: number;
    durationBasis?: "days" | "hours";
    duration?: number;
    averageWeeklyWorkHours?: number;
  };
  start: DateObj;
  end: DateObj;
};
export type MedicalLeaveContinuous = MedicalLeave & {
  type: "continuous";
  typeBasedDetails: {
    weeks: number;
  };
};
export type MedicalLeaveReduced = MedicalLeave & {
  type: "reduced";
  typeBasedDetails: {
    weeks: number;
    hoursPerWeek: number;
    averageWeeklyWorkHours: number;
  };
};
export type MedicalLeaveIntermittent = MedicalLeave & {
  type: "intermittent";
  typeBasedDetails: {
    frequencyIntervalBasis: "weeks" | "months" | "every6Months";
    frequency: number;
    durationBasis: "days" | "hours";
    duration: number;
    averageWeeklyWorkHours: number;
  };
};
export type MedicalClaim = {
  type: "medical";
  dueToPregnancy: boolean;
  providerForm?: string;
  leave:
    | MedicalLeaveContinuous
    | MedicalLeaveReduced
    | MedicalLeaveIntermittent;
};
export type FamilyClaim = {
  type: "childBonding" | "careForFamilyMember" | "pregnancyMaternity";
};

export type Employer = MassEmployer | UnemployedEmployer | SelfEmployedEmployer;
type MassEmployer = {
  type: "employed";
  fein: string;
  employerNotified: boolean;
  employerNotificationDate: DateObj;
};
type UnemployedEmployer = {
  type: "unemployed";
};
type SelfEmployedEmployer = {
  type: "selfEmployed";
};

type OtherBenefits = {
  willUseEmployerBenefits: boolean;
  employerBenefitsUsed?: ReceivedBenefit[];
  willReceiveOtherIncome: boolean;
  otherIncomeSources?: OtherIncomeSource[];
  tookLeaveForQualifyingReason?: boolean;
};

export const BenefitKinds = ["accrued", "stDis", "permDis", "pfml"] as const;
export type BenefitKind = typeof BenefitKinds[number];
type Benefit = {
  kind: BenefitKind;
  dateStart: DateObj;
  dateEnd: DateObj;
};
type EnumBenefit = Benefit & { amount: number };
type PaidLeaveBenefit = Benefit & { kind: "accrued" };
type StandardDisabilityBenefit = EnumBenefit & { kind: "stDis" };
type PermanentDisabilityBenefit = EnumBenefit & { kind: "permDis" };
type FamilyMedicalBenefit = EnumBenefit & { kind: "pfml" };
export type ReceivedBenefit =
  | StandardDisabilityBenefit
  | PermanentDisabilityBenefit
  | PaidLeaveBenefit
  | FamilyMedicalBenefit;

export const IncomeSourceTypes = [
  "workersComp",
  "unemployment",
  "ssdi",
  "govRetDis",
  "jonesAct",
  "rrRet",
  "otherEmp",
  "selfEmp",
] as const;
export type IncomeSourceType = typeof IncomeSourceTypes[number];
type IncomeSource = {
  type: IncomeSourceType;
  dateStart: DateObj;
  dateEnd: DateObj;
  amount?: number;
};
type WorkersCompensation = IncomeSource & { type: "workersComp" };
type UnemploymentInsurance = IncomeSource & { type: "unemployment" };
type SocialSecurityDisabilityInsurance = IncomeSource & {
  type: "ssdi";
};
type GovRetirementPlanDisabilityBenefits = IncomeSource & {
  type: "govRetDis";
};
type JonesActBenefits = IncomeSource & { type: "jonesAct" };
type RailroadRetirementBenefits = IncomeSource & {
  type: "rrRet";
};
type OtherEmployerEarnings = IncomeSource & { type: "otherEmp" };
type SelfEmploymentEarnings = IncomeSource & { type: "selfEmp" };
export type OtherIncomeSource =
  | WorkersCompensation
  | UnemploymentInsurance
  | SocialSecurityDisabilityInsurance
  | GovRetirementPlanDisabilityBenefits
  | JonesActBenefits
  | RailroadRetirementBenefits
  | OtherEmployerEarnings
  | SelfEmploymentEarnings;

export const PaymentTypes = ["ach", "debit"] as const;
export type PaymentType = typeof PaymentTypes[number];
type AccountDetails = {
  routingNumber: number;
  accountNumber: number;
};
type DestinationAddress = {
  line1: string;
  line2: string;
  city: string;
  state: string;
  zip: number;
};
type Payment = { type: PaymentType };
type DirectDeposit = Payment & {
  type: "ach";
  accountDetails: AccountDetails;
};
type DebitCard = Payment & {
  type: "debit";
  destinationAddress: DestinationAddress;
};
export type PaymentInfo = DirectDeposit | DebitCard;
