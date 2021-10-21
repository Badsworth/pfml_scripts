import {
  ApiRequestError,
  AuthSessionMissingError,
  BadRequestError,
  ForbiddenError,
  InternalServerError,
  Issue,
  NetworkError,
  NotFoundError,
  RequestTimeoutError,
  ServiceUnavailableError,
  UnauthorizedError,
  ValidationError,
} from "../errors";
import { compact, isEmpty } from "lodash";
import { Auth } from "@aws-amplify/auth";
import tracker from "../services/tracker";

export interface ApiResponseBody<TResponseData> {
  data?: TResponseData;
  errors?: Issue[];
  meta?: {
    resource: string;
    method: string;
    query?: string;
    paging?: {
      page_offset: number;
      page_size: number;
      total_pages: number;
      total_records: number;
      order_by: string;
      order_direction: "ascending" | "descending";
    };
  };
  status_code: number;
  // API's validation warnings, such as missing required fields. These are "warnings"
  // because we expect some fields to be missing as the user proceeds page-by-page through the flow.
  warnings?: Issue[];
}
export type ApiMethod = "DELETE" | "GET" | "PATCH" | "POST" | "PUT";
export type ApiRequestBody = Record<string, unknown> | FormData;

/**
 * Class that implements the base interaction with API resources
 */
export default abstract class BaseApi {
  /**
   * Root path of API resource without leading slash.
   */
  abstract get basePath(): string;
  /**
   * Prefix used in ValidationError message strings.
   */
  abstract get i18nPrefix(): string;

  /**
   * Send an authenticated API request.
   * @example const { data } = await this.request<{ email: string }>("GET", "users/current");
   *          const email = data.email;
   */
  async request<TResponseData>(
    method: ApiMethod,
    subPath = "",
    body: ApiRequestBody | null = null,
    additionalHeaders = {},
    { excludeAuthHeader = false, multipartForm = false } = {}
  ) {
    const url = createRequestUrl(method, this.basePath, subPath, body);
    const authHeader = excludeAuthHeader ? {} : await getAuthorizationHeader();
    const headers = {
      ...authHeader,
      ...additionalHeaders,
    };

    if (!multipartForm) {
      // Normally we want "application/json", but when we upload files,
      // we want the browser to automatically set the "Content-Type" to
      // "multipart/form-data" (specifically, we want the browser to set
      // a "multipart/form-data" with a "boundary" value as a delimiter to
      // tell the API how to parse the body)
      // https://stackoverflow.com/questions/3508338/what-is-the-boundary-in-multipart-form-data
      // https://muffinman.io/uploading-files-using-fetch-multipart-form-data/
      headers["Content-Type"] = "application/json";
    }

    const response = await this.sendRequest<TResponseData>(url, {
      body: method === "GET" || !body ? null : createRequestBody(body),
      headers,
      method,
    });

    return response;
  }

  /**
   * Send a request and handle the response
   */
  async sendRequest<TResponseData>(url: string, options: RequestInit) {
    let response: Response;
    let responseBody: ApiResponseBody<TResponseData>;

    try {
      tracker.trackFetchRequest(url);
      response = await fetch(url, options);
      tracker.markFetchRequestEnd();
      responseBody = await response.json();
    } catch (error) {
      handleError(error);
    }

    const { data, errors, meta, warnings } = responseBody;
    if (!response.ok) {
      handleNotOkResponse(response, errors, this.i18nPrefix, data);
    }

    return {
      data,
      meta,
      // Guaranteeing warnings is always an array makes our code simpler
      warnings: formatIssues(warnings) || [],
    };
  }
}

/**
 * Transform the request body into a format that fetch expects
 */
function createRequestBody(payload?: ApiRequestBody): XMLHttpRequestBodyInit {
  if (payload instanceof FormData) {
    return payload;
  }

  return JSON.stringify(payload);
}

/**
 * Create the full URL for a given API path
 * @param method
 * @param basePath - Root path of API resource without leading slash
 * @param subPath - relative path without a leading forward slash
 * @param body
 */
export function createRequestUrl(
  method: ApiMethod,
  basePath: string,
  subPath: string,
  body?: ApiRequestBody
) {
  // Remove leading slash from apiPath if it has one
  const cleanedPaths = compact([basePath, subPath]).map(removeLeadingSlash);
  let url = [process.env.apiUrl, ...cleanedPaths].join("/");

  if (method === "GET" && body && !(body instanceof FormData)) {
    // Append query string to URL
    const searchBody = {};
    Object.entries(body).forEach(([key, value]) => {
      const stringValue =
        typeof value === "string" ? value : JSON.stringify(value);
      searchBody[key] = stringValue;
    });

    const params = new URLSearchParams(searchBody).toString();
    url = `${url}?${params}`;
  }

  return url;
}

/**
 * Retrieve auth token header
 */
export async function getAuthorizationHeader() {
  try {
    const session = await Auth.currentSession();
    const jwtToken = session.getAccessToken().getJwtToken();
    return { Authorization: `Bearer ${jwtToken}` };
  } catch (error) {
    // Amplify returns a string for the error...
    const message = error instanceof Error ? error.message : error;
    throw new AuthSessionMissingError(message);
  }
}

/**
 * Convert API error/warnings field paths into a field path format we use on the Portal
 */
function formatIssues(issues?: Issue[]) {
  if (!issues) return issues;

  return issues.map((issue) => {
    if (!issue.field) return issue;

    // Convert dot-notation for array indexes into square bracket notation,
    // which is how we format our array fields.
    // For example foo.12 => foo[12]
    const field = issue.field.replace(/\.(\d+)(\.)?/g, "[$1]$2");

    return {
      ...issue,
      field,
    };
  });
}

/**
 * Handle request errors
 */
export function handleError(error: unknown) {
  // Request failed to send or something failed while parsing the response
  // Log the JS error to support troubleshooting
  console.error(error);
  throw new NetworkError(error instanceof Error ? error.message : "");
}

/**
 * Throw an error when the API returns a non-2xx response status code
 * @param url
 * @param response
 * @param errors - Issues returned by the API
 * @param i18nPrefix - Prefix used in ValidationError message strings
 * @param data
 */
export function handleNotOkResponse(
  response: Response,
  errors: Issue[] = [],
  i18nPrefix: string,
  data?: unknown
) {
  if (isEmpty(errors)) {
    // Response didn't include any errors that we could use to
    // display user friendly error message(s) from, so throw
    // an error based on the status code
    // For Leave Admin permission issues, response data is needed to determine page routing
    throwError(response, data);
  } else {
    throw new ValidationError(formatIssues(errors), i18nPrefix);
  }
}

/**
 * Remove leading slash
 */
function removeLeadingSlash(path: string) {
  return path.replace(/^\//, "");
}

const throwError = (response: Response, data: unknown = {}) => {
  const { status } = response;
  const message = `${status} status code received`;

  switch (status) {
    case 400:
      throw new BadRequestError(data, message);
    case 401:
      throw new UnauthorizedError(data, message);
    case 403:
      throw new ForbiddenError(data, message);
    case 404:
      throw new NotFoundError(data, message);
    case 408:
      throw new RequestTimeoutError(data, message);
    case 500:
      throw new InternalServerError(data, message);
    case 503:
      throw new ServiceUnavailableError(data, message);
    default:
      throw new ApiRequestError(data, message);
  }
};
