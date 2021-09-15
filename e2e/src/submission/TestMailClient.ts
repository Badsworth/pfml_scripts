import { GraphQLClient, gql } from "graphql-request";
import fetch, { RequestInfo, RequestInit } from "node-fetch";
import AbortController from "abort-controller";
import { formatDuration } from "date-fns";

export type Email = {
  id: string;
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
  messageWildcard?: string;
  timestamp_from?: number;
  debugInfo?: Record<string, string>;
  timeout?: number;
};
type Filter = { field: string; match: string; action: string; value: string };

export default class TestMailClient {
  namespace: string;
  headers: Record<string, string>;
  apiKey: string;
  timeout: number;

  constructor(apiKey: string, namespace: string, timeout = 60000) {
    this.headers = { Authorization: `Bearer ${apiKey}` };
    this.timeout = timeout;
    this.apiKey = apiKey;
    this.namespace = namespace;
  }

  async getEmails(opts: GetEmailsOpts): Promise<Email[]> {
    // We instantiate a new client for every call. This is the only way to share a single timeout across multiple
    // API calls (ie: we may make 5 requests, but we want to time out 120s from the time we started making calls).
    const controller = new AbortController();
    const timeout = setTimeout(
      () => controller.abort(),
      opts.timeout ?? this.timeout
    );
    const client = new GraphQLClient("https://api.testmail.app/api/graphql", {
      headers: this.headers,
      fetch: (url: RequestInfo, init: RequestInit = {}) =>
        fetch(url, { ...init, signal: controller.signal }),
    });

    try {
      const emails = await this._getMatchingEmails(client, opts);
      clearTimeout(timeout); // Clear the timeout to avoid hanging processes.
      return emails;
    } catch (e) {
      clearTimeout(timeout); // Clear the timeout to avoid hanging processes.
      throw e;
    }
  }

  /**
   * This method wraps our e-mail fetching to add additional functionality (body wildcard matching).
   *
   * If we've requested a message wildcard, we first query for all messages that match, then check to see if any of
   * the messages returned match the message wildcard. If they don't, we go back and look for more, excluding the
   * ones we've already found.
   */
  private async _getMatchingEmails(
    client: GraphQLClient,
    opts: GetEmailsOpts
  ): Promise<Email[]> {
    const { messageWildcard } = opts;
    if (messageWildcard === undefined) {
      // For non-wildcard searches, use the basic logic.
      return this._fetchEmails(opts, client);
    }

    let excludedIds: string[] = [];
    while (true) {
      const candidates = await this._fetchEmails(opts, client, excludedIds);
      const matches = candidates.filter((email) =>
        email.html.includes(messageWildcard)
      );
      if (matches.length > 0) {
        return matches;
      }
      // Exclude these IDs from our next search, as we already know they're not matching.
      excludedIds = excludedIds.concat(candidates.map((e) => e.id));
    }
  }

  private async _fetchEmails(
    opts: GetEmailsOpts,
    client: GraphQLClient,
    excludedIds: string[] = []
  ): Promise<Email[]> {
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
    // Exclude any IDs we've specifically requested be excluded from this search.
    excludedIds.forEach((id) => {
      filters.push({
        field: "id",
        match: "exact",
        action: "exclude",
        value: id,
      });
    });
    const tag = this.getTagFromAddress(opts.address);
    const variables = {
      tag: tag,
      namespace: this.namespace,
      advanced_filters: filters,
      timestamp_from: opts.timestamp_from,
    };
    try {
      const response = await client.request(unifiedQuery, {
        ...variables,
        livequery: true,
      });
      return response.inbox.emails;
    } catch (e) {
      if (e.name === "AbortError") {
        const searchParams = new URLSearchParams({
          query: unifiedQuery,
          // Note: variables and headers can't currently be read from the query string in GraphiQL.
        });
        const debugInfo = {
          "GraphQL URL": `https://api.testmail.app/api/graphql?${searchParams}`,
          "GraphQL Variables": JSON.stringify(
            // For debugging, add timestamp_to to variables, so the window is accurate.
            { ...variables, timestamp_to: Date.now() },
            undefined,
            4
          ),
          "GraphQL Headers": JSON.stringify(this.headers, undefined, 4),
          ...opts.debugInfo,
        };
        const timeoutDuration = {
          seconds: Math.round((opts.timeout || this.timeout) / 1000),
        };
        throw new Error(
          `Timed out while looking for e-mail after ${formatDuration(
            timeoutDuration
          )}. This can happen when an e-mail is taking a long time to arrive, the e-mail was never sent, or you're looking for the wrong message.

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
    $timestamp_to: Float
    $livequery: Boolean
  ) {
    inbox(
      namespace: $namespace
      tag: $tag
      advanced_filters: $advanced_filters
      timestamp_from: $timestamp_from
      timestamp_to: $timestamp_to
      limit: 100
      livequery: $livequery
    ) {
      result
      message
      emails {
        id
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
