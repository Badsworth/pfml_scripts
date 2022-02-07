/**
 * DO NOT MODIFY
 * Generated using @spec2ts/openapi-client.
 * See https://www.npmjs.com/package/@spec2ts/openapi-client
 */

/* eslint-disable */

export const defaults: RequestOptions = {
  baseUrl: "/v1",
};
export const servers = {
  developmentServer: "/v1",
};
export type RequestOptions = {
  baseUrl?: string;
  fetch?: typeof fetch;
  headers?: Record<string, string | undefined>;
} & Omit<RequestInit, "body" | "headers">;
export type ApiResponse<T> = {
  status: number;
  statusText: string;
  headers: Record<string, string>;
  data: T;
};
type Encoders = Array<(s: string) => string>;
type TagFunction = (strings: TemplateStringsArray, ...values: any[]) => string;
type FetchRequestOptions = RequestOptions & {
  body?: string | FormData;
};
type JsonRequestOptions = RequestOptions & {
  body: unknown;
};
type FormRequestOptions<T extends Record<string, unknown>> = RequestOptions & {
  body: T;
};
type MultipartRequestOptions = RequestOptions & {
  body: Record<string, any>; // string | Blob
};
/** Utilities functions */
export const _ = {
  // Encode param names and values as URIComponent
  encodeReserved: [encodeURI, encodeURIComponent],
  allowReserved: [encodeURI, encodeURI],
  /** Deeply remove all properties with undefined values. */
  stripUndefined<T extends Record<string, U | undefined>, U>(
    obj?: T,
  ): Record<string, U> | undefined {
    return obj && JSON.parse(JSON.stringify(obj));
  },
  isEmpty(v: unknown): boolean {
    return typeof v === "object" && !!v
      ? Object.keys(v).length === 0 && v.constructor === Object
      : v === undefined;
  },
  /** Creates a tag-function to encode template strings with the given encoders. */
  encode(encoders: Encoders, delimiter = ","): TagFunction {
    return (strings: TemplateStringsArray, ...values: any[]) => {
      return strings.reduce(
        (prev, s, i) => `${prev}${s}${q(values[i] ?? "", i)}`,
        "",
      );
    };
    function q(v: any, i: number): string {
      const encoder = encoders[i % encoders.length];
      if (typeof v === "object") {
        if (Array.isArray(v)) {
          return v.map(encoder).join(delimiter);
        }
        const flat = Object.entries(v).reduce(
          (flat, entry) => [...flat, ...entry],
          [] as any,
        );
        return flat.map(encoder).join(delimiter);
      }
      return encoder(String(v));
    }
  },
  /** Separate array values by the given delimiter. */
  delimited(
    delimiter = ",",
  ): (params: Record<string, any>, encoders?: Encoders) => string {
    return (params: Record<string, any>, encoders = _.encodeReserved) =>
      Object.entries(params)
        .filter(([, value]) => !_.isEmpty(value))
        .map(([name, value]) => _.encode(encoders, delimiter)`${name}=${value}`)
        .join("&");
  },
  /** Join URLs parts. */
  joinUrl(...parts: Array<string | undefined>): string {
    return parts
      .filter(Boolean)
      .join("/")
      .replace(/([^:]\/)\/+/, "$1");
  },
};
/** Functions to serialize query parameters in different styles. */
export const QS = {
  /** Join params using an ampersand and prepends a questionmark if not empty. */
  query(...params: string[]): string {
    const s = params.filter((p) => !!p).join("&");
    return s && `?${s}`;
  },
  /**
   * Serializes nested objects according to the `deepObject` style specified in
   * https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#style-values
   */
  deep(params: Record<string, any>, [k, v] = _.encodeReserved): string {
    const qk = _.encode([(s) => s, k]);
    const qv = _.encode([(s) => s, v]);
    // don't add index to arrays
    // https://github.com/expressjs/body-parser/issues/289
    const visit = (obj: any, prefix = ""): string =>
      Object.entries(obj)
        .filter(([, v]) => !_.isEmpty(v))
        .map(([prop, v]) => {
          const isValueObject = typeof v === "object";
          const index = Array.isArray(obj) && !isValueObject ? "" : prop;
          const key = prefix ? qk`${prefix}[${index}]` : prop;
          if (isValueObject) {
            return visit(v, key);
          }
          return qv`${key}=${v}`;
        })
        .join("&");
    return visit(params);
  },
  /**
   * Property values of type array or object generate separate parameters
   * for each value of the array, or key-value-pair of the map.
   * For other types of properties this property has no effect.
   * See https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#encoding-object
   */
  explode(params: Record<string, any>, encoders = _.encodeReserved): string {
    const q = _.encode(encoders);
    return Object.entries(params)
      .filter(([, value]) => typeof value !== "undefined")
      .map(([name, value]) => {
        if (Array.isArray(value)) {
          return value.map((v) => q`${name}=${v}`).join("&");
        }
        if (typeof value === "object") {
          return QS.explode(value, encoders);
        }
        return q`${name}=${value}`;
      })
      .join("&");
  },
  form: _.delimited(),
  pipe: _.delimited("|"),
  space: _.delimited("%20"),
};
/** Http request base methods. */
export const http = {
  async fetch(
    url: string,
    req?: FetchRequestOptions,
  ): Promise<ApiResponse<string | undefined>> {
    const {
      baseUrl,
      headers,
      fetch: customFetch,
      ...init
    } = { ...defaults, ...req };
    const href = _.joinUrl(baseUrl, url);
    const res = await (customFetch || fetch)(href, {
      ...init,
      headers: _.stripUndefined({ ...defaults.headers, ...headers }),
    });
    let text: string | undefined;
    try {
      text = await res.text();
    } catch (err) {
      /* ok */
    }
    if (!res.ok) {
      throw new HttpError(res.status, res.statusText, href, res.headers, text);
    }
    return {
      status: res.status,
      statusText: res.statusText,
      headers: http.headers(res.headers),
      data: text,
    };
  },
  async fetchJson(
    url: string,
    req: FetchRequestOptions = {},
  ): Promise<ApiResponse<any>> {
    const res = await http.fetch(url, {
      ...req,
      headers: {
        ...req.headers,
        Accept: "application/json",
      },
    });
    res.data = res.data && JSON.parse(res.data);
    return res;
  },
  async fetchVoid(
    url: string,
    req: FetchRequestOptions = {},
  ): Promise<ApiResponse<undefined>> {
    const res = await http.fetch(url, {
      ...req,
      headers: {
        ...req.headers,
        Accept: "application/json",
      },
    });
    return res as ApiResponse<undefined>;
  },
  json({ body, headers, ...req }: JsonRequestOptions): FetchRequestOptions {
    return {
      ...req,
      body: JSON.stringify(body),
      headers: {
        ...headers,
        "Content-Type": "application/json",
      },
    };
  },
  form<T extends Record<string, unknown>>({
    body,
    headers,
    ...req
  }: FormRequestOptions<T>): FetchRequestOptions {
    return {
      ...req,
      body: QS.form(body),
      headers: {
        ...headers,
        "Content-Type": "application/x-www-form-urlencoded",
      },
    };
  },
  multipart({ body, ...req }: MultipartRequestOptions): FetchRequestOptions {
    const data = new FormData();
    Object.entries(body).forEach(([name, value]) => {
      data.append(name, value);
    });
    return {
      ...req,
      body: data,
    };
  },
  headers(headers: Headers): Record<string, string> {
    const res: Record<string, string> = {};
    headers.forEach((value, key) => (res[key] = value));
    return res;
  },
};
export class HttpError extends Error {
  status: number;
  statusText: string;
  headers: Record<string, string>;
  data?: Record<string, unknown>;
  constructor(
    status: number,
    statusText: string,
    url: string,
    headers: Headers,
    text?: string,
  ) {
    super(`${url} - ${statusText} (${status})`);
    this.status = status;
    this.statusText = statusText;
    this.headers = http.headers(headers);
    if (text) {
      try {
        this.data = JSON.parse(text);
      } catch (err) {
        /* ok */
      }
    }
  }
}
/** Utility Type to extract returns type from a method. */
export type ApiResult<Fn> = Fn extends (
  ...args: any
) => Promise<ApiResponse<infer T>>
  ? T
  : never;
export interface Meta {
  resource: string;
  method: string;
  query?: object;
  paging?: {
    page_offset?: number;
    page_size?: number;
    total_records?: number;
    total_pages?: number;
    order_by?: string;
    order_direction?: string;
  };
}
export interface ValidationErrorDetail {
  type?: string;
  message?: string;
  rule?: (string | number | number | boolean | any | object) | null;
  field?: string | null;
}
export interface SuccessfulResponse {
  status_code: number;
  message?: string;
  meta?: Meta;
  data?: any | object;
  warnings?: ValidationErrorDetail[];
}
export interface ErrorResponse {
  status_code: number;
  message?: string;
  meta?: Meta;
  data?: any | object;
  warnings?: ValidationErrorDetail[];
  errors: ValidationErrorDetail[];
}
export interface Flag {
  start?: string | null;
  end?: string | null;
  name?: string;
  updated_at?: string | null;
  options?: object;
  enabled?: boolean;
}
export type FlagsResponse = Flag[];
export type Fein = string;
export interface UserCreateRequest {
  email_address?: string | null;
  password?: string | null;
  role?: {
    role_description?: "Claimant" | "Employer";
  };
  user_leave_administrator?: {
    employer_fein?: Fein | null;
  } | null;
}
export interface MaskedPhone {
  int_code?: string;
  phone_number?: string;
  phone_type?: "Cell" | "Fax" | "Phone";
}
export interface RoleResponse {
  role_id?: number;
  role_description?: string;
}
export interface UserLeaveAdminResponse {
  employer_id?: string;
  employer_fein?: string;
  employer_dba?: string | null;
  has_fineos_registration?: boolean;
  verified?: boolean;
}
export interface UserResponse {
  user_id?: string;
  auth_id?: string;
  email_address?: string;
  application_names?: {
    first_name?: string | null;
    middle_name?: string | null;
    last_name?: string | null;
  }[];
  mfa_delivery_preference?: ("SMS" | "Opt Out") | null;
  mfa_phone_number?: MaskedPhone | null;
  consented_to_data_sharing?: boolean;
  roles?: RoleResponse[];
  user_leave_administrators?: UserLeaveAdminResponse[];
}
export interface RoleUserDeleteRequest {
  role: {
    role_description: string;
  };
  user_id: string;
}
export interface EmployerAddFeinRequestBody {
  employer_fein?: Fein | null;
}
export interface Phone {
  int_code?: string | null;
  phone_number?: string | null;
  phone_type?: ("Cell" | "Fax" | "Phone") | null;
}
export interface UserUpdateRequest {
  consented_to_data_sharing?: boolean;
  mfa_delivery_preference?: ("SMS" | "Opt Out") | null;
  mfa_phone_number?: Phone;
}
export type SsnItin = string;
export type MassId = string;
export type MaskedDate = string;
export interface EmployeeResponse {
  employee_id: string;
  first_name?: string;
  middle_name?: string | null;
  other_name?: string | null;
  email_address?: string | null;
  last_name?: string;
  phone_numbers?: (Phone | null)[];
  tax_identifier_last4?: string | null;
  tax_identifier?: SsnItin | null;
  fineos_customer_number?: string | null;
  mass_id_number?: MassId | null;
  date_of_birth?: MaskedDate | null;
}
export interface GETEmployeesByEmployeeIdResponse extends SuccessfulResponse {
  data?: EmployeeResponse;
}
export type EmployeeErrorResponse = object;
export interface EmployeeUpdateRequest {
  first_name?: string;
  middle_name?: string;
  last_name?: string;
  email_address?: string;
}
export interface PATCHEmployeesByEmployeeIdResponse extends SuccessfulResponse {
  data?: EmployeeResponse;
}
export interface EmployeeSearchRequest {
  first_name: string;
  middle_name?: string;
  last_name: string;
  tax_identifier_last4: string;
}
export interface POSTEmployeesSearchResponse extends SuccessfulResponse {
  data?: EmployeeResponse;
}
export interface EmployerResponse {
  employer_id?: string;
  employer_fein?: string;
  employer_dba?: string | null;
}
export interface POSTEmployersAddResponse extends SuccessfulResponse {
  data?: EmployerResponse;
}
export interface POSTEmployersAddResponse402 extends ErrorResponse {}
export interface POSTEmployersAddResponse409 extends ErrorResponse {}
export interface POSTEmployersAddResponse503 extends ErrorResponse {}
export interface WithholdingResponse {
  filing_period?: any;
}
export interface GETEmployersWithholdingByEmployerIdResponse
  extends SuccessfulResponse {
  data?: WithholdingResponse;
}
export interface EmployeeBasicResponse {
  employee_id: string;
  first_name?: string;
  middle_name?: string | null;
  last_name?: string;
  other_name?: string | null;
}
export interface AbsencePeriodResponse {
  absence_period_start_date?: string;
  absence_period_end_date?: string;
  reason?:
    | "Care for a Family Member"
    | "Pregnancy/Maternity"
    | "Child Bonding"
    | "Serious Health Condition - Employ";
  reason_qualifier_one?: "Newborn" | "Adoption" | "Foster Care";
  reason_qualifier_two?: string;
  period_type?: "Continuous" | "Intermittent" | "Reduced Schedule";
  request_decision?: "Pending" | "Approved" | "Denied" | "Withdrawn";
  fineos_leave_request_id?: number;
}
export interface EvidenceStatusDetail {
  document_name?: string;
  is_document_received?: boolean;
}
export interface DetailedClaimResponse {
  employer?: EmployerResponse;
  employee?: EmployeeBasicResponse;
  application_id?: string;
  fineos_absence_id?: any;
  fineos_notification_id?: any;
  created_at?: any;
  absence_periods?: AbsencePeriodResponse[];
  outstanding_evidence?: {
    employee_evidence?: EvidenceStatusDetail[];
    employer_evidence?: EvidenceStatusDetail[];
  };
  has_paid_payments?: boolean;
}
export interface GETClaimsByFineosAbsenceIdResponse extends SuccessfulResponse {
  data?: DetailedClaimResponse;
}
export interface ManagedRequirementResponse {
  follow_up_date?: any;
  responded_at?: any;
  status?: string | null;
  category?: string | null;
  type?: string | null;
  created_at?: any;
}
export interface ClaimResponse {
  employer?: EmployerResponse;
  employee?: EmployeeBasicResponse;
  fineos_absence_id?: any;
  fineos_notification_id?: any;
  absence_period_start_date?: any;
  absence_period_end_date?: any;
  claim_status?: any;
  claim_type_description?: any;
  organization_unit_id?: string;
  created_at?: any;
  managed_requirements?: ManagedRequirementResponse[];
  absence_periods?: AbsencePeriodResponse[];
  has_paid_payments?: boolean;
}
export type ClaimsResponse = ClaimResponse[];
export interface GETClaimsResponse extends SuccessfulResponse {
  data?: ClaimsResponse;
}
export interface PaymentResponse {
  payment_id?: string | null;
  period_start_date?: any;
  period_end_date?: any;
  amount?: number | null;
  sent_to_bank_date?: string | null;
  payment_method?: ("Elec Funds Transfer" | "Check" | "Debit") | null;
  expected_send_date_start?: string | null;
  expected_send_date_end?: string | null;
  cancellation_date?: string | null;
  status?: "Sent to bank" | "Pending" | "Cancelled" | "Delayed";
}
export interface PaymentsResponse {
  absence_case_id?: any;
  payments?: PaymentResponse[];
}
export interface GETPaymentsResponse extends SuccessfulResponse {
  data?: PaymentsResponse;
}
export interface ClaimDocumentResponse {
  created_at: string | null;
  document_type:
    | "State managed Paid Leave Confirmation"
    | "Approval Notice"
    | "Request for More information"
    | "Denial Notice"
    | "Employer Response Additional Documentation"
    | "Own serious health condition form"
    | "Pregnancy/Maternity form"
    | "Child bonding evidence form"
    | "Care for a family member form"
    | "Military exigency form"
    | "Pending Application Withdrawn"
    | "Appeal Acknowledgment"
    | "Maximum Weekly Benefit Change Notice"
    | "Benefit Amount Change Notice"
    | "Leave Allotment Change Notice"
    | "Approved Time Cancelled"
    | "Change Request Approved"
    | "Change Request Denied";
  content_type: string | null;
  fineos_document_id: string;
  name: string | null;
  description: string | null;
}
export interface GETEmployersClaimsByFineosAbsenceIdDocumentsResponse
  extends SuccessfulResponse {
  data?: ClaimDocumentResponse;
}
export type Date = string;
export interface ConcurrentLeave {
  concurrent_leave_id?: string | null;
  is_for_current_employer?: boolean | null;
  leave_end_date?: Date | null;
  leave_start_date?: Date | null;
}
export interface EmployerBenefit {
  employer_benefit_id?: string | null;
  benefit_start_date?: Date | null;
  benefit_end_date?: Date | null;
  benefit_amount_dollars?: number | null;
  benefit_amount_frequency?:
    | ("Per Day" | "Per Week" | "Per Month" | "In Total" | "Unknown")
    | null;
  benefit_type?:
    | (
        | "Accrued paid leave"
        | "Short-term disability insurance"
        | "Permanent disability insurance"
        | "Family or medical leave insurance"
        | "Unknown"
      )
    | null;
  is_full_salary_continuous?: boolean | null;
}
export interface EmployerContinuousLeavePeriods {
  start_date?: Date;
  end_date?: Date;
}
export interface EmployerIntermittentLeavePeriods {
  start_date?: Date;
  end_date?: Date;
  frequency?: number | null;
  frequency_interval?: number | null;
  frequency_interval_basis?: ("Days" | "Weeks" | "Months") | null;
  duration?: number | null;
  duration_basis?: ("Minutes" | "Hours" | "Days") | null;
}
export interface EmployerReducedScheduleLeavePeriods {
  start_date?: Date;
  end_date?: Date;
}
export interface EmployerLeaveDetails {
  reason?: string | null;
  continuous_leave_periods?: EmployerContinuousLeavePeriods;
  intermittent_leave_periods?: EmployerIntermittentLeavePeriods;
  reduced_schedule_leave_periods?: EmployerReducedScheduleLeavePeriods;
}
export interface PreviousLeave {
  previous_leave_id?: string | null;
  is_for_current_employer?: boolean | null;
  leave_end_date?: Date | null;
  leave_start_date?: Date | null;
  leave_reason?:
    | (
        | "Pregnancy"
        | "Caring for a family member with a serious health condition"
        | "Bonding with my child after birth or placement"
        | "Caring for a family member who serves in the armed forces"
        | "Managing family affairs while a family member is on active duty in the armed forces"
        | "Unknown"
        | "An illness or injury"
      )
    | null;
  worked_per_week_minutes?: number | null;
  leave_minutes?: number | null;
  type?: ("other_reason" | "same_reason") | null;
}
export interface Address {
  city?: string | null;
  line_1?: string | null;
  line_2?: string | null;
  state?: string | null;
  zip?: string | null;
}
export type MaskedSsnItin = string;
export interface ClaimReviewResponse {
  concurrent_leave?: ConcurrentLeave | null;
  date_of_birth?: MaskedDate;
  employer_benefits: EmployerBenefit[];
  employer_dba: string | null;
  employer_id: string;
  employer_fein: Fein;
  fineos_absence_id: string;
  first_name?: string;
  hours_worked_per_week?: string;
  last_name?: string;
  leave_details: EmployerLeaveDetails;
  status: string;
  middle_name?: string;
  uses_second_eform_version: boolean;
  previous_leaves: PreviousLeave[];
  residential_address: Address;
  tax_identifier?: MaskedSsnItin;
  absence_periods: AbsencePeriodResponse[];
  managed_requirements?: ManagedRequirementResponse[];
}
export interface GETEmployersClaimsByFineosAbsenceIdReviewResponse
  extends SuccessfulResponse {
  data?: ClaimReviewResponse;
}
export interface EmployerClaimRequestBody {
  uses_second_eform_version?: boolean;
  employer_benefits: EmployerBenefit[];
  concurrent_leave?: ConcurrentLeave | null;
  previous_leaves: PreviousLeave[];
  has_amendments?: boolean;
  hours_worked_per_week: number | null;
  employer_decision?: "Approve" | "Deny" | "Requires More Information";
  fraud?: "Yes" | "No";
  comment?: string;
  leave_reason?: string | null;
  believe_relationship_accurate?: ("Yes" | "No" | "Unknown") | null;
  relationship_inaccurate_reason?: string | null;
}
export interface UpdateClaimReviewResponse {
  claim_id: string;
}
export interface PATCHEmployersClaimsByFineosAbsenceIdReviewResponse
  extends SuccessfulResponse {
  data?: UpdateClaimReviewResponse;
}
export interface OrganizationUnit {
  organization_unit_id: string;
  name: string;
}
export interface ReducedScheduleLeavePeriods {
  leave_period_id?: string | null;
  start_date?: Date | null;
  end_date?: Date | null;
  thursday_off_minutes?: number | null;
  friday_off_minutes?: number | null;
  saturday_off_minutes?: number | null;
  sunday_off_minutes?: number | null;
  monday_off_minutes?: number | null;
  tuesday_off_minutes?: number | null;
  wednesday_off_minutes?: number | null;
}
export interface ContinuousLeavePeriods {
  leave_period_id?: string | null;
  start_date?: Date | null;
  end_date?: Date | null;
  last_day_worked?: Date | null;
  expected_return_to_work_date?: Date | null;
  start_date_full_day?: boolean | null;
  start_date_off_hours?: number | null;
  start_date_off_minutes?: number | null;
  end_date_off_hours?: number | null;
  end_date_off_minutes?: number | null;
  end_date_full_day?: boolean | null;
}
export interface IntermittentLeavePeriods {
  leave_period_id?: string | null;
  start_date?: Date | null;
  end_date?: Date | null;
  frequency?: number | null;
  frequency_interval?: number | null;
  frequency_interval_basis?: ("Days" | "Weeks" | "Months") | null;
  duration?: number | null;
  duration_basis?: ("Minutes" | "Hours" | "Days") | null;
}
export type DateOrMaskedDate = string;
export interface CaringLeaveMetadata {
  family_member_first_name?: string | null;
  family_member_middle_name?: string | null;
  family_member_last_name?: string | null;
  family_member_date_of_birth?: DateOrMaskedDate | null;
  relationship_to_caregiver?:
    | (
        | "Parent"
        | "Child"
        | "Grandparent"
        | "Grandchild"
        | "Other Family Member"
        | "Service Member"
        | "Inlaw"
        | "Sibling - Brother/Sister"
        | "Other"
        | "Spouse"
      )
    | null;
}
export interface ApplicationLeaveDetails {
  reason?:
    | (
        | "Pregnancy/Maternity"
        | "Child Bonding"
        | "Serious Health Condition - Employee"
        | "Care for a Family Member"
      )
    | null;
  reason_qualifier?: ("Newborn" | "Adoption" | "Foster Care") | null;
  reduced_schedule_leave_periods?: ReducedScheduleLeavePeriods[] | null;
  continuous_leave_periods?: ContinuousLeavePeriods[] | null;
  intermittent_leave_periods?: IntermittentLeavePeriods[] | null;
  caring_leave_metadata?: CaringLeaveMetadata;
  pregnant_or_recent_birth?: boolean | null;
  child_birth_date?: DateOrMaskedDate | null;
  child_placement_date?: DateOrMaskedDate | null;
  has_future_child_date?: boolean | null;
  employer_notified?: boolean | null;
  employer_notification_date?: Date | null;
  employer_notification_method?:
    | ("In Writing" | "In Person" | "By Telephone" | "Other")
    | null;
}
export type RoutingNbr = string;
export interface PaymentPreference {
  payment_method?: ("Elec Funds Transfer" | "Check" | "Debit") | null;
  account_number?: string | null;
  routing_number?: RoutingNbr | null;
  bank_account_type?: ("Checking" | "Savings") | null;
}
export type DayOfWeek =
  | "Sunday"
  | "Monday"
  | "Tuesday"
  | "Wednesday"
  | "Thursday"
  | "Friday"
  | "Saturday";
export interface WorkPatternDay {
  day_of_week?: DayOfWeek;
  week_number?: number;
  minutes?: number | null;
}
export interface WorkPattern {
  work_pattern_type?: ("Fixed" | "Rotating" | "Variable") | null;
  work_week_starts?: DayOfWeek | null;
  pattern_start_date?: Date | null;
  work_pattern_days?: WorkPatternDay[] | null;
}
export interface OtherIncome {
  other_income_id?: string | null;
  income_start_date?: Date | null;
  income_end_date?: Date | null;
  income_amount_dollars?: number | null;
  income_amount_frequency?:
    | ("Per Day" | "Per Week" | "Per Month" | "In Total")
    | null;
  income_type?:
    | (
        | "Workers Compensation"
        | "Unemployment Insurance"
        | "SSDI"
        | "Disability benefits under Gov't retirement plan"
        | "Jones Act benefits"
        | "Railroad Retirement benefits"
        | "Earnings from another employment/self-employment"
      )
    | null;
}
export interface ApplicationResponse {
  application_nickname?: string | null;
  organization_unit_id?: string | null;
  application_id?: string;
  fineos_absence_id?: string;
  tax_identifier?: MaskedSsnItin | null;
  employer_id?: string | null;
  employer_fein?: string | null;
  first_name?: string | null;
  middle_name?: string | null;
  last_name?: string | null;
  date_of_birth?: MaskedDate | null;
  has_continuous_leave_periods?: boolean | null;
  has_employer_benefits?: boolean | null;
  has_intermittent_leave_periods?: boolean | null;
  has_reduced_schedule_leave_periods?: boolean | null;
  has_other_incomes?: boolean | null;
  has_submitted_payment_preference?: boolean | null;
  has_state_id?: boolean | null;
  has_mailing_address?: boolean | null;
  mailing_address?: Address | null;
  residential_address?: Address | null;
  mass_id?: string | null;
  employment_status?: ("Employed" | "Unemployed" | "Self-Employed") | null;
  occupation?:
    | ("Sales Clerk" | "Administrative" | "Engineer" | "Health Care")
    | null;
  employee_organization_units?: OrganizationUnit[];
  employer_organization_units?: OrganizationUnit[];
  organization_unit?: OrganizationUnit | null;
  organization_unit_selection?: ("not_listed" | "not_selected") | null;
  gender?:
    | (
        | "Woman"
        | "Man"
        | "Non-binary"
        | "Gender not listed"
        | "Prefer not to answer"
      )
    | null;
  hours_worked_per_week?: number | null;
  leave_details?: ApplicationLeaveDetails | null;
  payment_preference?: PaymentPreference[] | null;
  work_pattern?: WorkPattern | null;
  employer_benefits?: EmployerBenefit[] | null;
  other_incomes?: OtherIncome[] | null;
  imported_from_fineos_at?: string | null;
  updated_at?: string;
  updated_time?: string;
  status?: "Started" | "Submitted" | "Completed";
  phone?: MaskedPhone;
  has_previous_leaves_other_reason?: boolean | null;
  has_previous_leaves_same_reason?: boolean | null;
  has_concurrent_leave?: boolean | null;
  previous_leaves_other_reason?: PreviousLeave[];
  previous_leaves_same_reason?: PreviousLeave[];
  concurrent_leave?: ConcurrentLeave | null;
  is_withholding_tax?: boolean | null;
}
export interface POSTApplicationsResponse extends SuccessfulResponse {
  data?: ApplicationResponse;
}
export type ApplicationSearchResults = ApplicationResponse[];
export interface GETApplicationsResponse extends SuccessfulResponse {
  data?: ApplicationSearchResults;
}
export interface ApplicationRequestBody {
  organization_unit_selection?: ("not_listed" | "not_selected") | null;
  organization_unit_id?: string | null;
  application_nickname?: string | null;
  tax_identifier?: SsnItin | null;
  employer_fein?: Fein | null;
  hours_worked_per_week?: number | null;
  first_name?: string | null;
  middle_name?: string | null;
  last_name?: string | null;
  date_of_birth?: DateOrMaskedDate | null;
  has_mailing_address?: boolean | null;
  mailing_address?: Address | null;
  residential_address?: Address | null;
  has_continuous_leave_periods?: boolean | null;
  has_employer_benefits?: boolean | null;
  has_intermittent_leave_periods?: boolean | null;
  has_other_incomes?: boolean | null;
  has_reduced_schedule_leave_periods?: boolean | null;
  has_state_id?: boolean | null;
  mass_id?: MassId | null;
  employment_status?: ("Employed" | "Unemployed" | "Self-Employed") | null;
  occupation?:
    | ("Sales Clerk" | "Administrative" | "Engineer" | "Health Care")
    | null;
  gender?:
    | (
        | "Woman"
        | "Man"
        | "Non-binary"
        | "Gender not listed"
        | "Prefer not to answer"
      )
    | null;
  leave_details?: ApplicationLeaveDetails;
  work_pattern?: WorkPattern | null;
  employer_benefits?: EmployerBenefit[] | null;
  other_incomes?: OtherIncome[] | null;
  phone?: Phone;
  has_previous_leaves_other_reason?: boolean | null;
  has_previous_leaves_same_reason?: boolean | null;
  has_concurrent_leave?: boolean | null;
  previous_leaves_other_reason?: PreviousLeave[] | null;
  previous_leaves_same_reason?: PreviousLeave[] | null;
  concurrent_leave?: ConcurrentLeave | null;
}
export interface PATCHApplicationsByApplicationIdResponse
  extends SuccessfulResponse {
  data?: ApplicationResponse;
}
export interface ApplicationImportRequestBody {
  absence_case_id?: string | null;
  tax_identifier?: SsnItin | null;
}
export interface POSTApplicationsImportResponse extends SuccessfulResponse {
  data?: ApplicationResponse;
}
export interface POSTApplicationsImportResponse503 extends ErrorResponse {
  data?: ApplicationResponse;
}
export interface POSTApplicationsByApplicationIdSubmitApplicationResponse
  extends SuccessfulResponse {
  data?: ApplicationResponse;
}
export interface POSTApplicationsByApplicationIdSubmitApplicationResponse503
  extends ErrorResponse {
  data?: ApplicationResponse;
}
export interface POSTApplicationsByApplicationIdCompleteApplicationResponse
  extends SuccessfulResponse {
  data?: ApplicationResponse;
}
export interface POSTApplicationsByApplicationIdCompleteApplicationResponse503
  extends ErrorResponse {
  data?: ApplicationResponse;
}
export interface DocumentResponse {
  user_id: string;
  application_id: string;
  created_at: any;
  document_type:
    | "Passport"
    | "Driver's License Mass"
    | "Driver's License Other State"
    | "Identification Proof"
    | "State managed Paid Leave Confirmation"
    | "Own serious health condition form"
    | "Pregnancy/Maternity form"
    | "Child bonding evidence form"
    | "Care for a family member form"
    | "Military exigency form"
    | "Pending Application Withdrawn"
    | "Appeal Acknowledgment"
    | "Maximum Weekly Benefit Change Notice"
    | "Benefit Amount Change Notice"
    | "Leave Allotment Change Notice"
    | "Approved Time Cancelled"
    | "Change Request Approved"
    | "Change Request Denied";
  content_type: string;
  fineos_document_id: string;
  name: string;
  description: string;
}
export interface GETApplicationsByApplicationIdDocumentsResponse
  extends SuccessfulResponse {
  data?: DocumentResponse[];
}
export interface DocumentUploadRequest {
  document_type:
    | "Passport"
    | "Driver's License Mass"
    | "Driver's License Other State"
    | "Identification Proof"
    | "State managed Paid Leave Confirmation"
    | "Approval Notice"
    | "Request for More information"
    | "Denial Notice"
    | "Own serious health condition form"
    | "Pregnancy/Maternity form"
    | "Child bonding evidence form"
    | "Care for a family member form"
    | "Military exigency form"
    | "Pending Application Withdrawn"
    | "Appeal Acknowledgment"
    | "Maximum Weekly Benefit Change Notice"
    | "Benefit Amount Change Notice"
    | "Leave Allotment Change Notice"
    | "Approved Time Cancelled"
    | "Change Request Approved"
    | "Change Request Denied"
    | "Certification Form";
  name?: string;
  description?: string;
  mark_evidence_received?: boolean;
  file: Blob;
}
export interface POSTApplicationsByApplicationIdDocumentsResponse
  extends SuccessfulResponse {
  data?: DocumentResponse;
}
export interface PaymentPreferenceRequestBody {
  payment_preference?: PaymentPreference;
}
export interface POSTApplicationsByApplicationIdSubmitPaymentPreferenceResponse
  extends SuccessfulResponse {
  data?: ApplicationResponse;
}
export interface TaxWithholdingPreferenceRequestBody {
  is_withholding_tax?: boolean | null;
}
export interface POSTApplicationsByApplicationIdSubmitTaxWithholdingPreferenceResponse
  extends SuccessfulResponse {
  data?: ApplicationResponse;
}
export interface EligibilityRequest {
  tax_identifier: SsnItin;
  employer_fein: Fein;
  leave_start_date: Date;
  application_submitted_date: Date;
  employment_status:
    | "Employed"
    | "Unemployed"
    | "Self-Employed"
    | "Unknown"
    | "Retired";
}
export interface EligibilityResponse {
  financially_eligible: boolean;
  description: string;
  total_wages?: number | null;
  state_average_weekly_wage?: number | null;
  unemployment_minimum?: number | null;
  employer_average_weekly_wage?: number | null;
}
export interface POSTFinancialEligibilityResponse extends SuccessfulResponse {
  data?: EligibilityResponse;
}
export interface RMVCheckRequest {
  absence_case_id: string;
  date_of_birth: Date;
  first_name: string;
  last_name: string;
  residential_address_city: string;
  residential_address_line_1: string;
  residential_address_line_2?: string | null;
  residential_address_zip_code: string;
  ssn_last_4: string;
  mass_id_number?: any;
}
export interface RMVCheckResponse {
  verified: boolean;
  description: string;
}
export interface POSTRmvCheckResponse extends SuccessfulResponse {
  data?: RMVCheckResponse;
}
export interface NotificationRecipient {
  first_name?: string;
  last_name?: string;
  full_name?: string;
  contact_id?: string;
  email_address?: string;
}
export interface NotificationClaimant {
  first_name?: string;
  last_name?: string;
  date_of_birth?: Date;
  customer_id?: string;
}
export interface NotificationRequest {
  absence_case_id: string;
  fein: string;
  organization_name: string;
  document_type?: string;
  trigger: string;
  source: "Self-Service" | "Call Center";
  recipient_type: "Claimant" | "Leave Administrator";
  recipients: NotificationRecipient[];
  claimant_info: NotificationClaimant;
}
export interface POSTNotificationsResponse extends SuccessfulResponse {}
export interface VerificationRequest {
  employer_id: string;
  withholding_amount: number;
  withholding_quarter: string;
}
export interface AuthURIResponse {
  auth_uri?: string;
  claims_challenge?: string | null;
  code_verifier?: string;
  nonce?: string;
  redirect_uri?: string;
  scope?: string[];
  state?: string;
}
export interface AuthCodeResponse {
  code?: string;
  session_state?: string;
  state?: string;
}
export interface AdminTokenRequest {
  auth_uri_res?: AuthURIResponse;
  auth_code_res?: AuthCodeResponse;
}
export interface AdminTokenResponse {
  access_token?: string;
  refresh_token?: string;
  id_token?: string;
}
export interface AdminUserResponse {
  sub_id?: string;
  first_name?: string;
  last_name?: string;
  email_address?: string;
  groups?: string[];
  permissions?: string[];
}
export interface AdminLogoutResponse {
  logout_uri?: string;
}
export type GETAdminUsersResponse = UserResponse[];
export interface FlagLog extends Flag {
  family_name?: string;
  given_name?: string;
  created_at?: string;
}
export type FlagLogsResponse = FlagLog[];
/**
 * Get the API status
 */
export async function getStatus(
  options?: RequestOptions,
): Promise<ApiResponse<SuccessfulResponse>> {
  return await http.fetchJson("/status", {
    ...options,
  });
}
/**
 * Get feature flags
 */
export async function getFlags(
  options?: RequestOptions,
): Promise<ApiResponse<FlagsResponse>> {
  return await http.fetchJson("/flags", {
    ...options,
  });
}
/**
 * Get a feature flag
 */
export async function getFlagsByName(
  {
    name,
  }: {
    name: string;
  },
  options?: RequestOptions,
): Promise<ApiResponse<Flag>> {
  return await http.fetchJson(`/flags/${name}`, {
    ...options,
  });
}
/**
 * Create a User account
 */
export async function postUsers(
  userCreateRequest: UserCreateRequest,
  options?: RequestOptions,
): Promise<ApiResponse<UserResponse>> {
  return await http.fetchJson(
    "/users",
    http.json({
      ...options,
      method: "POST",
      body: userCreateRequest,
    }),
  );
}
/**
 * Remove a role from a user
 */
export async function deleteRoles(
  roleUserDeleteRequest: RoleUserDeleteRequest,
  options?: RequestOptions,
): Promise<ApiResponse<void>> {
  return await http.fetchVoid(
    "/roles",
    http.json({
      ...options,
      method: "DELETE",
      body: roleUserDeleteRequest,
    }),
  );
}
/**
 * Convert a User account to an employer role
 */
export async function postUsersByUser_idConvert_employer(
  {
    user_id,
  }: {
    user_id: string;
  },
  employerAddFeinRequestBody: EmployerAddFeinRequestBody,
  options?: RequestOptions,
): Promise<ApiResponse<UserResponse>> {
  return await http.fetchJson(
    `/users/${user_id}/convert_employer`,
    http.json({
      ...options,
      method: "POST",
      body: employerAddFeinRequestBody,
    }),
  );
}
/**
 * Retrieve a User account
 */
export async function getUsersByUser_id(
  {
    user_id,
  }: {
    user_id: string;
  },
  options?: RequestOptions,
): Promise<ApiResponse<UserResponse>> {
  return await http.fetchJson(`/users/${user_id}`, {
    ...options,
  });
}
/**
 * Update a User account
 */
export async function patchUsersByUser_id(
  {
    user_id,
  }: {
    user_id: string;
  },
  userUpdateRequest: UserUpdateRequest,
  options?: RequestOptions,
): Promise<ApiResponse<UserResponse>> {
  return await http.fetchJson(
    `/users/${user_id}`,
    http.json({
      ...options,
      method: "PATCH",
      body: userUpdateRequest,
    }),
  );
}
/**
 * Retrieve the User account corresponding to the currently authenticated user
 *
 */
export async function getUsersCurrent(
  options?: RequestOptions,
): Promise<ApiResponse<UserResponse>> {
  return await http.fetchJson("/users/current", {
    ...options,
  });
}
/**
 * Retrieve an Employee record
 */
export async function getEmployeesByEmployee_id(
  {
    employee_id,
  }: {
    employee_id: string;
  },
  options?: RequestOptions,
): Promise<ApiResponse<GETEmployeesByEmployeeIdResponse>> {
  return await http.fetchJson(`/employees/${employee_id}`, {
    ...options,
  });
}
/**
 * Update an Employee record, for mutable properties
 */
export async function patchEmployeesByEmployee_id(
  {
    employee_id,
  }: {
    employee_id: string;
  },
  employeeUpdateRequest: EmployeeUpdateRequest,
  options?: RequestOptions,
): Promise<ApiResponse<PATCHEmployeesByEmployeeIdResponse>> {
  return await http.fetchJson(
    `/employees/${employee_id}`,
    http.json({
      ...options,
      method: "PATCH",
      body: employeeUpdateRequest,
    }),
  );
}
/**
 * Lookup an Employee by SSN/ITIN and name
 */
export async function postEmployeesSearch(
  employeeSearchRequest: EmployeeSearchRequest,
  options?: RequestOptions,
): Promise<ApiResponse<POSTEmployeesSearchResponse>> {
  return await http.fetchJson(
    "/employees/search",
    http.json({
      ...options,
      method: "POST",
      body: employeeSearchRequest,
    }),
  );
}
/**
 * Add an FEIN to the logged in Leave Administrator
 */
export async function postEmployersAdd(
  employerAddFeinRequestBody: EmployerAddFeinRequestBody,
  options?: RequestOptions,
): Promise<ApiResponse<POSTEmployersAddResponse>> {
  return await http.fetchJson(
    "/employers/add",
    http.json({
      ...options,
      method: "POST",
      body: employerAddFeinRequestBody,
    }),
  );
}
/**
 * Retrieves the last withholding date for the FEIN specified
 */
export async function getEmployersWithholdingByEmployer_id(
  {
    employer_id,
  }: {
    employer_id: string;
  },
  options?: RequestOptions,
): Promise<ApiResponse<GETEmployersWithholdingByEmployerIdResponse>> {
  return await http.fetchJson(`/employers/withholding/${employer_id}`, {
    ...options,
  });
}
/**
 * Retrieve a claim for a specified absence ID
 */
export async function getClaimsByFineos_absence_id(
  {
    fineos_absence_id,
  }: {
    fineos_absence_id: string;
  },
  options?: RequestOptions,
): Promise<ApiResponse<GETClaimsByFineosAbsenceIdResponse>> {
  return await http.fetchJson(`/claims/${fineos_absence_id}`, {
    ...options,
  });
}
/**
 * Retrieve claims
 */
export async function getClaims(
  {
    page_size,
    page_offset,
    order_by,
    order_direction,
    employer_id,
    employee_id,
    claim_status,
    search,
    allow_hrd,
  }: {
    page_size?: number;
    page_offset?: number;
    order_by?: "fineos_absence_status" | "created_at" | "employee";
    order_direction?: "ascending" | "descending";
    employer_id?: string;
    employee_id?: string[];
    claim_status?: string;
    search?: string;
    allow_hrd?: boolean;
  } = {},
  options?: RequestOptions,
): Promise<ApiResponse<GETClaimsResponse>> {
  return await http.fetchJson(
    `/claims${QS.query(
      QS.form({
        page_size,
        page_offset,
        order_by,
        order_direction,
        employer_id,
        employee_id,
        claim_status,
        search,
        allow_hrd,
      }),
    )}`,
    {
      ...options,
    },
  );
}
/**
 * Retrieve payments with status for a specified absence ID
 */
export async function getPayments(
  {
    absence_case_id,
  }: {
    absence_case_id: string;
  },
  options?: RequestOptions,
): Promise<ApiResponse<GETPaymentsResponse>> {
  return await http.fetchJson(
    `/payments${QS.query(
      QS.form({
        absence_case_id,
      }),
    )}`,
    {
      ...options,
    },
  );
}
/**
 * Retrieve a FINEOS documents for a specified absence ID and document ID
 */
export async function getEmployersClaimsByFineos_absence_idDocumentsAndFineos_document_id(
  {
    fineos_absence_id,
    fineos_document_id,
  }: {
    fineos_absence_id: string;
    fineos_document_id: string;
  },
  options?: RequestOptions,
): Promise<ApiResponse<string | undefined>> {
  return await http.fetch(
    `/employers/claims/${fineos_absence_id}/documents/${fineos_document_id}`,
    {
      ...options,
    },
  );
}
/**
 * Retrieve a list of FINEOS documents for a specified absence ID
 */
export async function getEmployersClaimsByFineos_absence_idDocuments(
  {
    fineos_absence_id,
  }: {
    fineos_absence_id: string;
  },
  options?: RequestOptions,
): Promise<ApiResponse<GETEmployersClaimsByFineosAbsenceIdDocumentsResponse>> {
  return await http.fetchJson(
    `/employers/claims/${fineos_absence_id}/documents`,
    {
      ...options,
    },
  );
}
/**
 * Retrieve FINEOS claim review data for a specified absence ID
 */
export async function getEmployersClaimsByFineos_absence_idReview(
  {
    fineos_absence_id,
  }: {
    fineos_absence_id: string;
  },
  options?: RequestOptions,
): Promise<ApiResponse<GETEmployersClaimsByFineosAbsenceIdReviewResponse>> {
  return await http.fetchJson(`/employers/claims/${fineos_absence_id}/review`, {
    ...options,
  });
}
/**
 * Save review claim from leave admin
 */
export async function patchEmployersClaimsByFineos_absence_idReview(
  {
    fineos_absence_id,
  }: {
    fineos_absence_id: string;
  },
  employerClaimRequestBody: EmployerClaimRequestBody,
  options?: RequestOptions,
): Promise<ApiResponse<PATCHEmployersClaimsByFineosAbsenceIdReviewResponse>> {
  return await http.fetchJson(
    `/employers/claims/${fineos_absence_id}/review`,
    http.json({
      ...options,
      method: "PATCH",
      body: employerClaimRequestBody,
    }),
  );
}
/**
 * Create an Application
 */
export async function postApplications(
  options?: RequestOptions,
): Promise<ApiResponse<POSTApplicationsResponse>> {
  return await http.fetchJson("/applications", {
    ...options,
    method: "POST",
  });
}
/**
 * Retrieve all Applications for the specified user
 */
export async function getApplications(
  options?: RequestOptions,
): Promise<ApiResponse<GETApplicationsResponse>> {
  return await http.fetchJson("/applications", {
    ...options,
  });
}
/**
 * Retrieve an Application identified by the application id
 */
export async function getApplicationsByApplication_id(
  {
    application_id,
  }: {
    application_id: string;
  },
  options?: RequestOptions,
): Promise<ApiResponse<ApplicationResponse>> {
  return await http.fetchJson(`/applications/${application_id}`, {
    ...options,
  });
}
/**
 * Update an Application
 */
export async function patchApplicationsByApplication_id(
  {
    application_id,
  }: {
    application_id: string;
  },
  applicationRequestBody: ApplicationRequestBody,
  options?: RequestOptions,
): Promise<ApiResponse<PATCHApplicationsByApplicationIdResponse>> {
  return await http.fetchJson(
    `/applications/${application_id}`,
    http.json({
      ...options,
      method: "PATCH",
      body: applicationRequestBody,
    }),
  );
}
/**
 * Creates a new application in the PFML database from a FINEOS application that was created through the contact center.
 *
 */
export async function postApplicationsImport(
  applicationImportRequestBody: ApplicationImportRequestBody,
  options?: RequestOptions,
): Promise<ApiResponse<POSTApplicationsImportResponse>> {
  return await http.fetchJson(
    "/applications/import",
    http.json({
      ...options,
      method: "POST",
      body: applicationImportRequestBody,
    }),
  );
}
/**
 * Submit the first part of the application to the Claims Processing System.
 *
 */
export async function postApplicationsByApplication_idSubmit_application(
  {
    application_id,
  }: {
    application_id: string;
  },
  options?: RequestOptions,
): Promise<
  ApiResponse<POSTApplicationsByApplicationIdSubmitApplicationResponse>
> {
  return await http.fetchJson(
    `/applications/${application_id}/submit_application`,
    {
      ...options,
      method: "POST",
    },
  );
}
/**
 * Complete intake of an application in the Claims Processing System.
 *
 */
export async function postApplicationsByApplication_idComplete_application(
  {
    application_id,
  }: {
    application_id: string;
  },
  options?: RequestOptions,
): Promise<
  ApiResponse<POSTApplicationsByApplicationIdCompleteApplicationResponse>
> {
  return await http.fetchJson(
    `/applications/${application_id}/complete_application`,
    {
      ...options,
      method: "POST",
    },
  );
}
/**
 * Download an application (case) document by id.
 */
export async function getApplicationsByApplication_idDocumentsAndDocument_id(
  {
    application_id,
    document_id,
  }: {
    application_id: string;
    document_id: string;
  },
  options?: RequestOptions,
): Promise<ApiResponse<string | undefined>> {
  return await http.fetch(
    `/applications/${application_id}/documents/${document_id}`,
    {
      ...options,
    },
  );
}
/**
 * Get list of documents for a case
 */
export async function getApplicationsByApplication_idDocuments(
  {
    application_id,
  }: {
    application_id: string;
  },
  options?: RequestOptions,
): Promise<ApiResponse<GETApplicationsByApplicationIdDocumentsResponse>> {
  return await http.fetchJson(`/applications/${application_id}/documents`, {
    ...options,
  });
}
/**
 * Upload Document
 */
export async function postApplicationsByApplication_idDocuments(
  {
    application_id,
  }: {
    application_id: string;
  },
  documentUploadRequest: DocumentUploadRequest,
  options?: RequestOptions,
): Promise<ApiResponse<POSTApplicationsByApplicationIdDocumentsResponse>> {
  return await http.fetchJson(
    `/applications/${application_id}/documents`,
    http.multipart({
      ...options,
      method: "POST",
      body: documentUploadRequest,
    }),
  );
}
/**
 * Submit Payment Preference
 */
export async function postApplicationsByApplication_idSubmit_payment_preference(
  {
    application_id,
  }: {
    application_id: string;
  },
  paymentPreferenceRequestBody: PaymentPreferenceRequestBody,
  options?: RequestOptions,
): Promise<
  ApiResponse<POSTApplicationsByApplicationIdSubmitPaymentPreferenceResponse>
> {
  return await http.fetchJson(
    `/applications/${application_id}/submit_payment_preference`,
    http.json({
      ...options,
      method: "POST",
      body: paymentPreferenceRequestBody,
    }),
  );
}
/**
 * Submit Tax Withholding Preference
 */
export async function postApplicationsByApplication_idSubmit_tax_withholding_preference(
  {
    application_id,
  }: {
    application_id: string;
  },
  taxWithholdingPreferenceRequestBody: TaxWithholdingPreferenceRequestBody,
  options?: RequestOptions,
): Promise<
  ApiResponse<POSTApplicationsByApplicationIdSubmitTaxWithholdingPreferenceResponse>
> {
  return await http.fetchJson(
    `/applications/${application_id}/submit_tax_withholding_preference`,
    http.json({
      ...options,
      method: "POST",
      body: taxWithholdingPreferenceRequestBody,
    }),
  );
}
/**
 * Retrieve financial eligibility by SSN/ITIN, FEIN, leave start date, application submitted date and employment status.
 */
export async function postFinancialEligibility(
  eligibilityRequest: EligibilityRequest,
  options?: RequestOptions,
): Promise<ApiResponse<POSTFinancialEligibilityResponse>> {
  return await http.fetchJson(
    "/financial-eligibility",
    http.json({
      ...options,
      method: "POST",
      body: eligibilityRequest,
    }),
  );
}
/**
 * Perform lookup and data matching for information on RMV-issued IDs
 */
export async function postRmvCheck(
  rmvCheckRequest: RMVCheckRequest,
  options?: RequestOptions,
): Promise<ApiResponse<POSTRmvCheckResponse>> {
  return await http.fetchJson(
    "/rmv-check",
    http.json({
      ...options,
      method: "POST",
      body: rmvCheckRequest,
    }),
  );
}
/**
 * Send a notification that a document is available for a claimant to either the claimant or leave administrator.
 *
 */
export async function postNotifications(
  notificationRequest: NotificationRequest,
  options?: RequestOptions,
): Promise<ApiResponse<POSTNotificationsResponse>> {
  return await http.fetchJson(
    "/notifications",
    http.json({
      ...options,
      method: "POST",
      body: notificationRequest,
    }),
  );
}
/**
 * Check to see if user should be verified and create verification record
 *
 */
export async function postEmployersVerifications(
  verificationRequest: VerificationRequest,
  options?: RequestOptions,
): Promise<ApiResponse<UserResponse>> {
  return await http.fetchJson(
    "/employers/verifications",
    http.json({
      ...options,
      method: "POST",
      body: verificationRequest,
    }),
  );
}
/**
 * Returns azure ad authentication url to initiate user auth code flow
 */
export async function getAdminAuthorize(
  options?: RequestOptions,
): Promise<ApiResponse<AuthURIResponse>> {
  return await http.fetchJson("/admin/authorize", {
    ...options,
  });
}
/**
 * Trade an authentication code for an access token
 */
export async function postAdminToken(
  adminTokenRequest: AdminTokenRequest,
  options?: RequestOptions,
): Promise<ApiResponse<AdminTokenResponse>> {
  return await http.fetchJson(
    "/admin/token",
    http.json({
      ...options,
      method: "POST",
      body: adminTokenRequest,
    }),
  );
}
/**
 * Login as admin user
 */
export async function getAdminLogin(
  options?: RequestOptions,
): Promise<ApiResponse<AdminUserResponse>> {
  return await http.fetchJson("/admin/login", {
    ...options,
  });
}
/**
 * Logout admin user
 */
export async function getAdminLogout(
  options?: RequestOptions,
): Promise<ApiResponse<AdminLogoutResponse>> {
  return await http.fetchJson("/admin/logout", {
    ...options,
  });
}
/**
 * Retrieve all user accounts
 */
export async function getAdminUsers(
  {
    page_size,
    page_offset,
    email_address,
  }: {
    page_size?: number;
    page_offset?: number;
    email_address?: string;
  } = {},
  options?: RequestOptions,
): Promise<ApiResponse<GETAdminUsersResponse>> {
  return await http.fetchJson(
    `/admin/users${QS.query(
      QS.form({
        page_size,
        page_offset,
        email_address,
      }),
    )}`,
    {
      ...options,
    },
  );
}
/**
 * Update a feature flag
 */
export async function postAdminFlagsByName(
  {
    name,
  }: {
    name: string;
  },
  flag: Flag,
  options?: RequestOptions,
): Promise<ApiResponse<SuccessfulResponse>> {
  return await http.fetchJson(
    `/admin/flags/${name}`,
    http.json({
      ...options,
      method: "POST",
      body: flag,
    }),
  );
}
/**
 * Get feature flags
 */
export async function getAdminFlagsLogsByName(
  {
    name,
  }: {
    name: string;
  },
  options?: RequestOptions,
): Promise<ApiResponse<FlagLogsResponse>> {
  return await http.fetchJson(`/admin/flags/logs/${name}`, {
    ...options,
  });
}
