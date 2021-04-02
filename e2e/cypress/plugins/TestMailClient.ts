import { GraphQLClient, gql } from "graphql-request";
import fetch, { RequestInfo, RequestInit } from "node-fetch";
import AbortController from "abort-controller";

/**
 * Wrap the fetch function to give it a timeout.
 *
 * Without this, fetch against livequery APIs will just spin forever.
 */
const wrapFetchWithTimeout = (fetchProto: typeof fetch, timeout: number) => {
  return (url: RequestInfo, init?: RequestInit): ReturnType<typeof fetch> => {
    if (!init) {
      init = {};
    }
    const controller = new AbortController();
    init.signal = controller.signal;
    setTimeout(() => controller.abort(), timeout);
    return fetchProto(url, init);
  };
};

export type Email = {
  from: string;
  subject: string;
  text: string;
  html: string;
  timestamp: number;
};
export type GetEmailsOpts = {
  address: string;
  subject?: string;
  subjectWildcard?: string;
  timestamp_from?: number;
  debugInfo?: Record<string, string>;
};
type Filter = { field: string; match: string; action: string; value: string };

export default class TestMailClient {
  namespace: string;
  client: GraphQLClient;
  headers: Record<string, string>;
  apiKey: string;

  constructor(apiKey: string, namespace: string, timeout = 120000) {
    this.headers = { Authorization: `Bearer ${apiKey}` };
    this.client = new GraphQLClient("https://api.testmail.app/api/graphql", {
      headers: this.headers,
      // Limit the amount of time we'll wait for a response.
      fetch: wrapFetchWithTimeout(fetch, timeout),
    });
    this.apiKey = apiKey;
    this.namespace = namespace;
  }

  async getEmails(opts: GetEmailsOpts): Promise<Email[]> {
    const filters: Filter[] = [];

    if (opts.subject) {
      filters.push({
        field: "subject",
        match: "exact",
        action: "include",
        value: opts.subject,
      });
    }
    if (opts.subjectWildcard) {
      filters.push({
        field: "subject",
        match: "wildcard",
        action: "include",
        value: opts.subjectWildcard,
      });
    }
    const tag = this.getTagFromAddress(opts.address);
    const variables = {
      tag: tag,
      namespace: this.namespace,
      advanced_filters: filters,
      timestamp_from: opts.timestamp_from,
    };
    try {
      const response = await this.client.request(unifiedQuery, variables);
      return response.inbox.emails;
    } catch (e) {
      if (e.name === "AbortError") {
        const searchParams = new URLSearchParams({
          query: unifiedQuery,
          // Note: variables and headers can't currently be read from the query string in GraphiQL.
        });
        const debugInfo = {
          "GraphQL URL": `https://api.testmail.app/api/graphql?${searchParams}`,
          "GraphQL Variables": JSON.stringify(variables, undefined, 4),
          "GraphQL Headers": JSON.stringify(this.headers, undefined, 4),
          ...opts.debugInfo,
          timestamp_to: Date.now(),
        };
        throw new Error(
          `Timed out while looking for e-mail. This can happen when an e-mail is taking a long time to arrive, the e-mail was never sent, or you're looking for the wrong message.

          Debug information: 
          ------------------

          ${Object.entries(debugInfo)
            .map(([key, value]) => `${key}: ${value}`)
            .join("\n\n")}`
        );
      }
      throw e;
    }
  }

  /**
   * Fetch all emails matching a given tag and subject.
   */
  async getEmailsBySubject(address: string, subject: string): Promise<Email[]> {
    const response = await this.client.request(getEmailsBySubjectQuery, {
      tag: this.getTagFromAddress(address),
      subject,
      namespace: this.namespace,
    });
    return response.inbox.emails;
  }

  getTagFromAddress(address: string): string {
    const re = new RegExp(`^${this.namespace}\.(.*)@inbox\.testmail\.app$`);
    const match = address.match(re);
    if (!match || !(match[1].length > 0)) {
      throw new Error(
        `Oops, this doesn't look like a testmail address: ${address}`
      );
    }
    return match[1];
  }
}

/**
 * GraphQL queries:
 */
const unifiedQuery = gql`
  query getEmails(
    $namespace: String!
    $tag: String!
    $advanced_filters: [AdvancedFilter]
    $timestamp_from: Float
  ) {
    inbox(
      namespace: $namespace
      tag: $tag
      advanced_filters: $advanced_filters
      timestamp_from: $timestamp_from
      livequery: true
    ) {
      result
      message
      emails {
        timestamp
        from
        subject
        text
        html
      }
      count
    }
  }
`;
const getEmailsBySubjectQuery = gql`
  query getEmailsBySubject(
    $namespace: String!
    $tag: String!
    $subject: String!
  ) {
    inbox(
      namespace: $namespace
      tag: $tag
      livequery: true
      advanced_filters: [
        { field: subject, match: wildcard, action: include, value: $subject }
      ]
    ) {
      result
      message
      emails {
        from
        subject
        text
        html
      }
      count
    }
  }
`;
