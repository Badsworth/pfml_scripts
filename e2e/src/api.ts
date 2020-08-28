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
    body: object;
};
type MultipartRequestOptions = RequestOptions & {
    body: Record<string, string | Blob | undefined | any>;
};
/** Utilities functions */
export const _ = {
    // Encode param names and values as URIComponent
    encodeReserved: [encodeURIComponent, encodeURIComponent],
    allowReserved: [encodeURIComponent, encodeURI],
    /** Deeply remove all properties with undefined values. */
    stripUndefined<T>(obj?: T): T | undefined {
        return obj && JSON.parse(JSON.stringify(obj));
    },
    /** Creates a tag-function to encode template strings with the given encoders. */
    encode(encoders: Encoders, delimiter = ","): TagFunction {
        return (strings: TemplateStringsArray, ...values: any[]) => {
            return strings.reduce((prev, s, i) => `${prev}${s}${q(values[i] || "", i)}`, "");
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
            .filter(([, value]) => value !== undefined)
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
        const s = params.join("&");
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
            .filter(([, v]) => v !== undefined)
            .map(([prop, v]) => {
            const index = Array.isArray(obj) ? "" : prop;
            const key = prefix ? qk `${prefix}[${index}]` : prop;
            if (typeof v === "object") {
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
    form({ body, headers, ...req }: JsonRequestOptions): FetchRequestOptions {
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
    data?: object;
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
export interface GETStatusResponse {
    status?: string;
}
export interface UserResponse {
    user_id?: string;
    auth_id?: string;
    email_address?: string;
    consented_to_data_sharing?: boolean;
}
export interface Error {
    code: string;
    message: string;
}
export interface UserUpdateRequest {
    consented_to_data_sharing: boolean;
}
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
export interface ReducedScheduleLeavePeriods {
    leave_period_id?: string | null;
    start_date?: string | null;
    end_date?: string | null;
    is_estimated?: boolean | null;
    thursday_off_hours?: number | null;
    thursday_off_minutes?: number | null;
    friday_off_hours?: number | null;
    friday_off_minutes?: number | null;
    saturday_off_hours?: number | null;
    saturday_off_minutes?: number | null;
    sunday_off_hours?: number | null;
    sunday_off_minutes?: number | null;
    monday_off_hours?: number | null;
    monday_off_minutes?: number | null;
    tuesday_off_hours?: number | null;
    tuesday_off_minutes?: number | null;
    wednesday_off_hours?: number | null;
    wednesday_off_minutes?: number | null;
}
export interface ContinuousLeavePeriods {
    leave_period_id?: string | null;
    start_date?: string | null;
    end_date?: string | null;
    last_day_worked?: string | null;
    expected_return_to_work_date?: string | null;
    start_date_full_day?: boolean | null;
    start_date_off_hours?: number | null;
    start_date_off_minutes?: number | null;
    end_date_off_hours?: number | null;
    end_date_off_minutes?: number | null;
    end_date_full_day?: boolean | null;
    is_estimated?: boolean | null;
}
export interface IntermittentLeavePeriods {
    leave_period_id?: string | null;
    start_date?: string | null;
    end_date?: string | null;
    frequency?: number | null;
    frequency_interval?: number | null;
    frequency_interval_basis?: ("Days" | "Weeks" | "Months") | null;
    duration?: number | null;
    duration_basis?: ("Minutes" | "Hours" | "Days") | null;
}
export interface ApplicationLeaveDetails {
    reason?: ("Care For A Family Member" | "Pregnancy/Maternity" | "Child Bonding" | "Serious Health Condition - Employee") | null;
    reason_qualifier?: ("New Born" | "Serious Health Condition" | "Work Related Accident/Injury") | null;
    reduced_schedule_leave_periods?: ReducedScheduleLeavePeriods[];
    continuous_leave_periods?: ContinuousLeavePeriods[];
    intermittent_leave_periods?: IntermittentLeavePeriods[];
    relationship_to_caregiver?: ("Parent" | "Child" | "Grandparent" | "Grandchild" | "Other Family Member" | "Service Member" | "Inlaw" | "Sibling" | "Other") | null;
    relationship_qualifier?: ("Adoptive" | "Biological" | "Foster" | "Custodial Parent" | "Legal Guardian" | "Step Parent") | null;
    pregnant_or_recent_birth?: boolean | null;
    employer_notified?: boolean | null;
    employer_notification_date?: string | null;
    employer_notification_method?: ("In Writing" | "In Person" | "By Telephone" | "Other") | null;
}
export type RoutingNbr = string;
export interface ApplicationPaymentAccountDetails {
    account_number?: string | null;
    routing_number?: RoutingNbr | null;
    account_name?: string | null;
    account_type?: ("Checking" | "Savings") | null;
}
export interface ApplicationPaymentChequeDetails {
    name_to_print_on_check?: string | null;
}
export interface PaymentPreferences {
    payment_preference_id?: string | null;
    description?: string | null;
    payment_method?: ("ACH" | "Check" | "Gift Card") | null;
    is_default?: boolean | null;
    account_details?: ApplicationPaymentAccountDetails;
    cheque_details?: ApplicationPaymentChequeDetails;
}
export interface ApplicationResponse {
    application_nickname?: string | null;
    application_id?: string;
    tax_identifier_last4?: string | null;
    employer_id?: string | null;
    first_name?: string | null;
    middle_name?: string | null;
    last_name?: string | null;
    date_of_birth?: string | null;
    has_state_id?: boolean | null;
    mass_id?: string | null;
    employment_status?: ("Employed" | "Unemployed" | "Self-Employed") | null;
    occupation?: ("Sales Clerk" | "Administrative" | "Engineer" | "Health Care") | null;
    leave_details?: ApplicationLeaveDetails | null;
    payment_preferences?: PaymentPreferences[] | null;
    updated_time?: string;
    status?: "Started" | "Completed" | "Submitted";
}
export interface POSTApplicationsResponse extends SuccessfulResponse {
    data?: ApplicationResponse;
}
export type ApplicationSearchResults = ApplicationResponse[];
export interface GETApplicationsResponse extends SuccessfulResponse {
    data?: ApplicationSearchResults;
}
export type SsnItin = string;
export type Fein = string;
export type MassId = string;
export interface ApplicationRequestBody {
    application_nickname?: string | null;
    employee_ssn?: SsnItin | null;
    employer_fein?: Fein | null;
    first_name?: string | null;
    middle_name?: string | null;
    last_name?: string | null;
    date_of_birth?: string | null;
    has_state_id?: boolean | null;
    mass_id?: MassId | null;
    employment_status?: ("Employed" | "Unemployed" | "Self-Employed") | null;
    occupation?: ("Sales Clerk" | "Administrative" | "Engineer" | "Health Care") | null;
    leave_details?: ApplicationLeaveDetails;
    payment_preferences?: PaymentPreferences[];
}
export interface PATCHApplicationsByApplicationIdResponse extends SuccessfulResponse {
    data?: ApplicationResponse;
}
export interface POSTApplicationsByApplicationIdSubmitApplicationResponse extends SuccessfulResponse {
    data?: ApplicationResponse;
}
/**
 * Get the API status
 */
export async function getStatus(options?: RequestOptions): Promise<ApiResponse<GETStatusResponse>> {
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
 * Signal the data entry is complete and the application is ready to be submitted to the Claims Processing System.
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
