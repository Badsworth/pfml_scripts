/**
 * DO NOT MODIFY
 * Generated using @spec2ts/openapi-client.
 * See https://www.npmjs.com/package/@spec2ts/openapi-client
 */

/* eslint-disable */

export const defaults: RequestOptions = {
    baseUrl: "/v1"
};
export const servers = {
    developmentServer: "/v1"
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
    stripUndefined<T>(obj?: T): T | undefined {
        return obj && JSON.parse(JSON.stringify(obj));
    },
    isEmpty(v: unknown): boolean {
        return typeof v === "object" && !!v ?
            Object.keys(v).length === 0 && v.constructor === Object :
            v === undefined;
    },
    /** Creates a tag-function to encode template strings with the given encoders. */
    encode(encoders: Encoders, delimiter = ","): TagFunction {
        return (strings: TemplateStringsArray, ...values: any[]) => {
            return strings.reduce((prev, s, i) => `${prev}${s}${q(values[i] ?? "", i)}`, "");
        };
        function q(v: any, i: number): string {
            const encoder = encoders[i % encoders.length];
            if (typeof v === "object") {
                if (Array.isArray(v)) {
                    return v.map(encoder).join(delimiter);
                }
                const flat = Object.entries(v).reduce((flat, entry) => [...flat, ...entry], [] as any);
                return flat.map(encoder).join(delimiter);
            }
            return encoder(String(v));
        }
    },
    /** Separate array values by the given delimiter. */
    delimited(delimiter = ","): (params: Record<string, any>, encoders?: Encoders) => string {
        return (params: Record<string, any>, encoders = _.encodeReserved) => Object.entries(params)
            .filter(([, value]) => !_.isEmpty(value))
            .map(([name, value]) => _.encode(encoders, delimiter) `${name}=${value}`)
            .join("&");
    },
    /** Join URLs parts. */
    joinUrl(...parts: Array<string | undefined>): string {
        return parts
            .filter(Boolean)
            .join("/")
            .replace(/([^:]\/)\/+/, "$1");
    }
};
/** Functions to serialize query parameters in different styles. */
export const QS = {
    /** Join params using an ampersand and prepends a questionmark if not empty. */
    query(...params: string[]): string {
        const s = params.filter(p => !!p).join("&");
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
        const visit = (obj: any, prefix = ""): string => Object.entries(obj)
            .filter(([, v]) => !_.isEmpty(v))
            .map(([prop, v]) => {
            const isValueObject = typeof v === "object";
            const index = Array.isArray(obj) && !isValueObject ? "" : prop;
            const key = prefix ? qk `${prefix}[${index}]` : prop;
            if (isValueObject) {
                return visit(v, key);
            }
            return qv `${key}=${v}`;
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
                return value.map((v) => q `${name}=${v}`).join("&");
            }
            if (typeof value === "object") {
                return QS.explode(value, encoders);
            }
            return q `${name}=${value}`;
        })
            .join("&");
    },
    form: _.delimited(),
    pipe: _.delimited("|"),
    space: _.delimited("%20"),
};
/** Http request base methods. */
export const http = {
    async fetch(url: string, req?: FetchRequestOptions): Promise<ApiResponse<string | undefined>> {
        const { baseUrl, headers, fetch: customFetch, ...init } = { ...defaults, ...req };
        const href = _.joinUrl(baseUrl, url);
        const res = await (customFetch || fetch)(href, {
            ...init,
            headers: _.stripUndefined({ ...defaults.headers, ...headers }),
        });
        let text: string | undefined;
        try {
            text = await res.text();
        }
        catch (err) { /* ok */ }
        if (!res.ok) {
            throw new HttpError(res.status, res.statusText, href, res.headers, text);
        }
        return {
            status: res.status,
            statusText: res.statusText,
            headers: http.headers(res.headers),
            data: text
        };
    },
    async fetchJson(url: string, req: FetchRequestOptions = {}): Promise<ApiResponse<any>> {
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
    async fetchVoid(url: string, req: FetchRequestOptions = {}): Promise<ApiResponse<undefined>> {
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
    form<T extends Record<string, unknown>>({ body, headers, ...req }: FormRequestOptions<T>): FetchRequestOptions {
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
        headers.forEach((value, key) => res[key] = value);
        return res;
    }
};
export class HttpError extends Error {
    status: number;
    statusText: string;
    headers: Record<string, string>;
    data?: Record<string, unknown>;
    constructor(status: number, statusText: string, url: string, headers: Headers, text?: string) {
        super(`${url} - ${statusText} (${status})`);
        this.status = status;
        this.statusText = statusText;
        this.headers = http.headers(headers);
        if (text) {
            try {
                this.data = JSON.parse(text);
            }
            catch (err) { /* ok */ }
        }
    }
}
/** Utility Type to extract returns type from a method. */
export type ApiResult<Fn> = Fn extends (...args: any) => Promise<ApiResponse<infer T>> ? T : never;
export interface Meta {
    resource: string;
    method: string;
    query?: object;
    paging?: {
        offset?: number;
        limit?: number;
        count?: number;
        total?: number;
    };
}
export interface Issue {
    "type": string;
    message: string;
    rule?: string | number | number | boolean | any | object;
    field?: string;
}
export interface SuccessfulResponse {
    status_code: number;
    message?: string;
    meta?: Meta;
    data?: any | object;
    warnings?: Issue[];
}
export interface ErrorResponse {
    status_code: number;
    message?: string;
    meta?: Meta;
    data?: any | object;
    warnings?: Issue[];
    errors: Issue[];
}
export interface UserResponse {
    user_id?: string;
    auth_id?: string;
    email_address?: string;
    consented_to_data_sharing?: boolean;
}
export interface UserUpdateRequest {
    consented_to_data_sharing: boolean;
}
export interface EmployeeResponse {
    employee_id: string;
    first_name?: string;
    middle_name?: string | null;
    other_name?: string | null;
    email_address?: string | null;
    last_name?: string;
    phone_number?: string | null;
    tax_identifier_last4: string;
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
    employer_id: string;
    employer_fein: string;
    employer_dba: string;
}
export interface GETEmployersByEmployerIdResponse extends SuccessfulResponse {
    data?: EmployerResponse;
}
export interface ClaimDocumentResponse {
    created_at: any;
    document_type: "Passport" | "Driver's License Mass" | "Driver's License Other State" | "Identification Proof" | "State managed Paid Leave Confirmation" | "Approval Notice" | "Request for More information" | "Denial Notice";
    content_type: string;
    fineos_document_id: string;
    name: string;
    description: string;
}
export interface GETEmployersClaimsByFineosAbsenceIdDocumentsResponse extends SuccessfulResponse {
    data?: ClaimDocumentResponse;
}
export type Date = string;
export interface EmployerBenefit {
    employer_benefit_id?: string | null;
    benefit_start_date?: Date;
    benefit_end_date?: Date;
    benefit_amount_dollars?: number | null;
    benefit_amount_frequency?: ("Per Day" | "Per Week" | "Per Month" | "In Total") | null;
    benefit_type?: ("Accrued paid leave" | "Short-term disability insurance" | "Permanent disability insurance" | "Family or medical leave insurance" | "Unknown") | null;
}
export type Fein = string;
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
    leave_end_date?: Date;
    leave_start_date?: Date;
    leave_type?: "Pregnancy/Maternity" | "Serious Health Condition" | "Care of Family Member" | "Child Bonding" | "Military Caregiver" | "Military Exigency Family";
}
export interface Address {
    city?: string | null;
    line_1?: string | null;
    line_2?: string | null;
    state?: string | null;
    zip?: string | null;
}
export type SsnItin = string;
export interface ClaimReviewResponse {
    date_of_birth?: Date;
    employer_benefits?: EmployerBenefit[];
    employer_fein?: Fein;
    fineos_absence_id?: string;
    first_name?: string;
    last_name?: string;
    leave_details?: EmployerLeaveDetails;
    middle_name?: string;
    previous_leaves?: PreviousLeave[];
    residential_address?: Address;
    tax_identifier?: SsnItin;
    follow_up_date?: Date;
}
export interface GETEmployersClaimsByFineosAbsenceIdReviewResponse extends SuccessfulResponse {
    data?: ClaimReviewResponse;
}
export interface EmployerClaimRequestBody {
    employer_benefits: EmployerBenefit[];
    previous_leaves: PreviousLeave[];
    hours_worked_per_week: number;
    employer_decision?: "Approve" | "Deny" | "Requires More Information";
    fraud?: "Yes" | "No";
    comment?: string;
}
export interface UpdateClaimReviewResponse {
    claim_id: string;
}
export interface PATCHEmployersClaimsByFineosAbsenceIdReviewResponse extends SuccessfulResponse {
    data?: UpdateClaimReviewResponse;
}
export type MaskedSsnItin = string;
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
export interface ApplicationLeaveDetails {
    reason?: ("Pregnancy/Maternity" | "Child Bonding" | "Serious Health Condition - Employee") | null;
    reason_qualifier?: ("Newborn" | "Adoption" | "Foster Care") | null;
    reduced_schedule_leave_periods?: ReducedScheduleLeavePeriods[] | null;
    continuous_leave_periods?: ContinuousLeavePeriods[] | null;
    intermittent_leave_periods?: IntermittentLeavePeriods[] | null;
    relationship_to_caregiver?: ("Parent" | "Child" | "Grandparent" | "Grandchild" | "Other Family Member" | "Service Member" | "Inlaw" | "Sibling" | "Other" | "Employee") | null;
    relationship_qualifier?: ("Adoptive" | "Biological" | "Foster" | "Custodial Parent" | "Legal Guardian" | "Step Parent") | null;
    pregnant_or_recent_birth?: boolean | null;
    child_birth_date?: Date | null;
    child_placement_date?: Date | null;
    has_future_child_date?: boolean | null;
    employer_notified?: boolean | null;
    employer_notification_date?: Date | null;
    employer_notification_method?: ("In Writing" | "In Person" | "By Telephone" | "Other") | null;
}
export type RoutingNbr = string;
export interface PaymentPreference {
    payment_method?: ("Elec Funds Transfer" | "Check" | "Debit") | null;
    account_number?: string | null;
    routing_number?: RoutingNbr | null;
    bank_account_type?: ("Checking" | "Savings") | null;
}
export type DayOfWeek = "Sunday" | "Monday" | "Tuesday" | "Wednesday" | "Thursday" | "Friday" | "Saturday";
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
    income_start_date?: Date;
    income_end_date?: Date;
    income_amount_dollars?: number | null;
    income_amount_frequency?: ("Per Day" | "Per Week" | "Per Month" | "In Total") | null;
    income_type?: ("Workers Compensation" | "Unemployment Insurance" | "SSDI" | "Disability benefits under Gov't retirement plan" | "Jones Act benefits" | "Railroad Retirement benefits" | "Earnings from another employment/self-employment") | null;
}
export interface MaskedPhone {
    int_code?: string;
    phone_number?: string;
    phone_type?: "Cell" | "Fax" | "Phone";
}
export interface ApplicationResponse {
    application_nickname?: string | null;
    application_id?: string;
    fineos_absence_id?: string;
    tax_identifier?: MaskedSsnItin | null;
    employer_id?: string | null;
    employer_fein?: string | null;
    first_name?: string | null;
    middle_name?: string | null;
    last_name?: string | null;
    date_of_birth?: Date | null;
    has_continuous_leave_periods?: boolean | null;
    has_employer_benefits?: boolean | null;
    has_intermittent_leave_periods?: boolean | null;
    has_reduced_schedule_leave_periods?: boolean | null;
    has_other_incomes?: boolean | null;
    has_submitted_payment_preference?: boolean | null;
    other_incomes_awaiting_approval?: boolean | null;
    has_state_id?: boolean | null;
    has_mailing_address?: boolean | null;
    mailing_address?: Address | null;
    residential_address?: Address | null;
    mass_id?: string | null;
    employment_status?: ("Employed" | "Unemployed" | "Self-Employed") | null;
    occupation?: ("Sales Clerk" | "Administrative" | "Engineer" | "Health Care") | null;
    hours_worked_per_week?: number | null;
    leave_details?: ApplicationLeaveDetails | null;
    payment_preference?: PaymentPreference[] | null;
    work_pattern?: WorkPattern | null;
    employer_benefits?: EmployerBenefit[] | null;
    other_incomes?: OtherIncome[] | null;
    updated_time?: string;
    status?: "Started" | "Submitted" | "Completed";
    phone?: MaskedPhone;
}
export interface POSTApplicationsResponse extends SuccessfulResponse {
    data?: ApplicationResponse;
}
export type ApplicationSearchResults = ApplicationResponse[];
export interface GETApplicationsResponse extends SuccessfulResponse {
    data?: ApplicationSearchResults;
}
export type MassId = string;
export interface Phone {
    int_code?: string;
    phone_number?: string;
    phone_type?: "Cell" | "Fax" | "Phone";
}
export interface ApplicationRequestBody {
    application_nickname?: string | null;
    employee_ssn?: SsnItin | null;
    tax_identifier?: SsnItin | null;
    employer_fein?: Fein | null;
    hours_worked_per_week?: number | null;
    first_name?: string | null;
    middle_name?: string | null;
    last_name?: string | null;
    date_of_birth?: Date | null;
    has_mailing_address?: boolean | null;
    mailing_address?: Address | null;
    residential_address?: Address | null;
    has_continuous_leave_periods?: boolean | null;
    has_employer_benefits?: boolean | null;
    has_intermittent_leave_periods?: boolean | null;
    has_other_incomes?: boolean | null;
    other_incomes_awaiting_approval?: boolean | null;
    has_reduced_schedule_leave_periods?: boolean | null;
    has_state_id?: boolean | null;
    mass_id?: MassId | null;
    employment_status?: ("Employed" | "Unemployed" | "Self-Employed") | null;
    occupation?: ("Sales Clerk" | "Administrative" | "Engineer" | "Health Care") | null;
    leave_details?: ApplicationLeaveDetails;
    work_pattern?: WorkPattern | null;
    employer_benefits?: EmployerBenefit[];
    other_incomes?: OtherIncome[];
    phone?: Phone;
}
export interface PATCHApplicationsByApplicationIdResponse extends SuccessfulResponse {
    data?: ApplicationResponse;
}
export interface POSTApplicationsByApplicationIdSubmitApplicationResponse extends SuccessfulResponse {
    data?: ApplicationResponse;
}
export interface POSTApplicationsByApplicationIdSubmitApplicationResponse503 extends ErrorResponse {
    data?: ApplicationResponse;
}
export interface POSTApplicationsByApplicationIdCompleteApplicationResponse extends SuccessfulResponse {
    data?: ApplicationResponse;
}
export interface POSTApplicationsByApplicationIdCompleteApplicationResponse503 extends ErrorResponse {
    data?: ApplicationResponse;
}
export interface DocumentResponse {
    user_id: string;
    application_id: string;
    created_at: any;
    document_type: "Passport" | "Driver's License Mass" | "Driver's License Other State" | "Identification Proof" | "State managed Paid Leave Confirmation";
    content_type: string;
    fineos_document_id: string;
    name: string;
    description: string;
}
export interface GETApplicationsByApplicationIdDocumentsResponse extends SuccessfulResponse {
    data?: DocumentResponse[];
}
export interface DocumentUploadRequest {
    document_type: "Passport" | "Driver's License Mass" | "Driver's License Other State" | "Identification Proof" | "State managed Paid Leave Confirmation" | "Approval Notice" | "Request for More information" | "Denial Notice";
    name?: string;
    description?: string;
    mark_evidence_received?: boolean;
    // This type has been changed from Blob to unknown to facilitate uploading documents
    file: unknown; 
}
export interface POSTApplicationsByApplicationIdDocumentsResponse extends SuccessfulResponse {
    data?: DocumentResponse;
}
export interface PaymentPreferenceRequestBody {
    payment_preference?: PaymentPreference;
}
export interface POSTApplicationsByApplicationIdSubmitPaymentPreferenceResponse extends SuccessfulResponse {
    data?: ApplicationResponse;
}
export interface EligibilityRequest {
    tax_identifier: SsnItin;
    employer_fein: Fein;
    leave_start_date: Date;
    application_submitted_date: Date;
    employment_status: "Employed" | "Unemployed" | "Self-Employed";
}
export interface EligibilityResponse {
    financially_eligible: boolean;
    description: string;
    total_wages?: number;
    state_average_weekly_wage?: number;
    unemployment_minimum?: number;
    employer_average_weekly_wage?: number;
}
export interface POSTFinancialEligibilityResponse extends SuccessfulResponse {
    data?: EligibilityResponse;
}
export interface RMVCheckRequest {
    absence_case_id: string;
    date_of_birth: Date;
    first_name: string;
    last_name: string;
    mass_id_number: MassId;
    residential_address_city: string;
    residential_address_line_1: string;
    residential_address_line_2?: string | null;
    residential_address_zip_code: string;
    ssn_last_4: string;
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
    fein?: string;
    organization_name?: string;
    document_type?: string;
    trigger: string;
    source: "Self-Service" | "Call Center";
    recipient_type: "Claimant" | "Leave Administrator";
    recipients: NotificationRecipient[];
    claimant_info: NotificationClaimant;
}
export interface POSTNotificationsResponse extends SuccessfulResponse {
}
/**
 * Get the API status
 */
export async function getStatus(options?: RequestOptions): Promise<ApiResponse<SuccessfulResponse>> {
    return await http.fetchJson("/status", {
        ...options
    });
}
/**
 * Retrieve a User account
 */
export async function getUsersByUserId({ userId }: {
    userId: string;
}, options?: RequestOptions): Promise<ApiResponse<UserResponse>> {
    return await http.fetchJson(`/users/${userId}`, {
        ...options
    });
}
/**
 * Update a User account
 */
export async function patchUsersByUserId({ userId }: {
    userId: string;
}, userUpdateRequest: UserUpdateRequest, options?: RequestOptions): Promise<ApiResponse<UserResponse>> {
    return await http.fetchJson(`/users/${userId}`, http.json({
        ...options,
        method: "PATCH",
        body: userUpdateRequest
    }));
}
/**
 * Retrieve the User account corresponding to the currently authenticated user
 *
 */
export async function getUsersCurrent(options?: RequestOptions): Promise<ApiResponse<UserResponse>> {
    return await http.fetchJson("/users/current", {
        ...options
    });
}
/**
 * Retrieve an Employee record
 */
export async function getEmployeesByEmployeeId({ employeeId }: {
    employeeId: string;
}, options?: RequestOptions): Promise<ApiResponse<GETEmployeesByEmployeeIdResponse>> {
    return await http.fetchJson(`/employees/${employeeId}`, {
        ...options
    });
}
/**
 * Update an Employee record, for mutable properties
 */
export async function patchEmployeesByEmployeeId({ employeeId }: {
    employeeId: string;
}, employeeUpdateRequest: EmployeeUpdateRequest, options?: RequestOptions): Promise<ApiResponse<PATCHEmployeesByEmployeeIdResponse>> {
    return await http.fetchJson(`/employees/${employeeId}`, http.json({
        ...options,
        method: "PATCH",
        body: employeeUpdateRequest
    }));
}
/**
 * Lookup an Employee by SSN/ITIN and name
 */
export async function postEmployeesSearch(employeeSearchRequest: EmployeeSearchRequest, options?: RequestOptions): Promise<ApiResponse<POSTEmployeesSearchResponse>> {
    return await http.fetchJson("/employees/search", http.json({
        ...options,
        method: "POST",
        body: employeeSearchRequest
    }));
}
/**
 * Retrieve an Employer record
 */
export async function getEmployersByEmployerId({ employerId }: {
    employerId: string;
}, options?: RequestOptions): Promise<ApiResponse<GETEmployersByEmployerIdResponse>> {
    return await http.fetchJson(`/employers/${employerId}`, {
        ...options
    });
}
/**
 * Retrieve a FINEOS documents for a specified absence ID and document ID
 */
export async function getEmployersClaimsByFineosAbsenceIdDocumentsAndFineosDocumentId({ fineosAbsenceId, fineosDocumentId }: {
    fineosAbsenceId: string;
    fineosDocumentId: string;
}, options?: RequestOptions): Promise<ApiResponse<string | undefined>> {
    return await http.fetch(`/employers/claims/${fineosAbsenceId}/documents/${fineosDocumentId}`, {
        ...options
    });
}
/**
 * Retrieve a list of FINEOS documents for a specified absence ID
 */
export async function getEmployersClaimsByFineosAbsenceIdDocuments({ fineosAbsenceId }: {
    fineosAbsenceId: string;
}, options?: RequestOptions): Promise<ApiResponse<GETEmployersClaimsByFineosAbsenceIdDocumentsResponse>> {
    return await http.fetchJson(`/employers/claims/${fineosAbsenceId}/documents`, {
        ...options
    });
}
/**
 * Retrieve FINEOS claim review data for a specified absence ID
 */
export async function getEmployersClaimsByFineosAbsenceIdReview({ fineosAbsenceId }: {
    fineosAbsenceId: string;
}, options?: RequestOptions): Promise<ApiResponse<GETEmployersClaimsByFineosAbsenceIdReviewResponse>> {
    return await http.fetchJson(`/employers/claims/${fineosAbsenceId}/review`, {
        ...options
    });
}
/**
 * Save review claim from leave admin
 */
export async function patchEmployersClaimsByFineosAbsenceIdReview({ fineosAbsenceId }: {
    fineosAbsenceId: string;
}, employerClaimRequestBody: EmployerClaimRequestBody, options?: RequestOptions): Promise<ApiResponse<PATCHEmployersClaimsByFineosAbsenceIdReviewResponse>> {
    return await http.fetchJson(`/employers/claims/${fineosAbsenceId}/review`, http.json({
        ...options,
        method: "PATCH",
        body: employerClaimRequestBody
    }));
}
/**
 * Create an Application
 */
export async function postApplications(options?: RequestOptions): Promise<ApiResponse<POSTApplicationsResponse>> {
    return await http.fetchJson("/applications", {
        ...options,
        method: "POST"
    });
}
/**
 * Retrieve all Applications for the specified user
 */
export async function getApplications(options?: RequestOptions): Promise<ApiResponse<GETApplicationsResponse>> {
    return await http.fetchJson("/applications", {
        ...options
    });
}
/**
 * Retrieve an Application identified by the application id
 */
export async function getApplicationsByApplicationId({ applicationId }: {
    applicationId: string;
}, options?: RequestOptions): Promise<ApiResponse<ApplicationResponse>> {
    return await http.fetchJson(`/applications/${applicationId}`, {
        ...options
    });
}
/**
 * Update an Application
 */
export async function patchApplicationsByApplicationId({ applicationId }: {
    applicationId: string;
}, applicationRequestBody: ApplicationRequestBody, options?: RequestOptions): Promise<ApiResponse<PATCHApplicationsByApplicationIdResponse>> {
    return await http.fetchJson(`/applications/${applicationId}`, http.json({
        ...options,
        method: "PATCH",
        body: applicationRequestBody
    }));
}
/**
 * Submit the first part of the application to the Claims Processing System.
 *
 */
export async function postApplicationsByApplicationIdSubmitApplication({ applicationId }: {
    applicationId: string;
}, options?: RequestOptions): Promise<ApiResponse<POSTApplicationsByApplicationIdSubmitApplicationResponse>> {
    return await http.fetchJson(`/applications/${applicationId}/submit_application`, {
        ...options,
        method: "POST"
    });
}
/**
 * Complete intake of an application in the Claims Processing System.
 *
 */
export async function postApplicationsByApplicationIdCompleteApplication({ applicationId }: {
    applicationId: string;
}, options?: RequestOptions): Promise<ApiResponse<POSTApplicationsByApplicationIdCompleteApplicationResponse>> {
    return await http.fetchJson(`/applications/${applicationId}/complete_application`, {
        ...options,
        method: "POST"
    });
}
/**
 * Download an application (case) document by id.
 */
export async function getApplicationsByApplicationIdDocumentsAndDocumentId({ applicationId, documentId }: {
    applicationId: string;
    documentId: string;
}, options?: RequestOptions): Promise<ApiResponse<string | undefined>> {
    return await http.fetch(`/applications/${applicationId}/documents/${documentId}`, {
        ...options
    });
}
/**
 * Get list of documents for a case
 */
export async function getApplicationsByApplicationIdDocuments({ applicationId }: {
    applicationId: string;
}, options?: RequestOptions): Promise<ApiResponse<GETApplicationsByApplicationIdDocumentsResponse>> {
    return await http.fetchJson(`/applications/${applicationId}/documents`, {
        ...options
    });
}
/**
 * Upload Document
 */
export async function postApplicationsByApplicationIdDocuments({ applicationId }: {
    applicationId: string;
}, documentUploadRequest: DocumentUploadRequest, options?: RequestOptions): Promise<ApiResponse<POSTApplicationsByApplicationIdDocumentsResponse>> {
    return await http.fetchJson(`/applications/${applicationId}/documents`, http.multipart({
        ...options,
        method: "POST",
        body: documentUploadRequest
    }));
}
/**
 * Submit Payment Preference
 */
export async function postApplicationsByApplicationIdSubmitPaymentPreference({ applicationId }: {
    applicationId: string;
}, paymentPreferenceRequestBody: PaymentPreferenceRequestBody, options?: RequestOptions): Promise<ApiResponse<POSTApplicationsByApplicationIdSubmitPaymentPreferenceResponse>> {
    return await http.fetchJson(`/applications/${applicationId}/submit_payment_preference`, http.json({
        ...options,
        method: "POST",
        body: paymentPreferenceRequestBody
    }));
}
/**
 * Retrieve financial eligibility by SSN/ITIN, FEIN, leave start date, application submitted date and employment status.
 */
export async function postFinancialEligibility(eligibilityRequest: EligibilityRequest, options?: RequestOptions): Promise<ApiResponse<POSTFinancialEligibilityResponse>> {
    return await http.fetchJson("/financial-eligibility", http.json({
        ...options,
        method: "POST",
        body: eligibilityRequest
    }));
}
/**
 * Perform lookup and data matching for information on RMV-issued IDs
 */
export async function postRmvCheck(rmvCheckRequest: RMVCheckRequest, options?: RequestOptions): Promise<ApiResponse<POSTRmvCheckResponse>> {
    return await http.fetchJson("/rmv-check", http.json({
        ...options,
        method: "POST",
        body: rmvCheckRequest
    }));
}
/**
 * Send a notification that a document is available for a claimant to either the claimant or leave administrator.
 *
 */
export async function postNotifications(notificationRequest: NotificationRequest, options?: RequestOptions): Promise<ApiResponse<POSTNotificationsResponse>> {
    return await http.fetchJson("/notifications", http.json({
        ...options,
        method: "POST",
        body: notificationRequest
    }));
}
