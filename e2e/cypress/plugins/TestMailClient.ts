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

type Email = {
  from: string;
  subject: string;
  text: string;
  html: string;
};

export default class TestMailClient {
  namespace: string;
  endpoint = "https://api.testmail.app/api/json";
  client: GraphQLClient;

  constructor(apiKey: string, namespace: string, timeout = 60000) {
    this.client = new GraphQLClient("https://api.testmail.app/api/graphql", {
      headers: { Authorization: `Bearer ${apiKey}` },
      // Limit the amount of time we'll wait for a response.
      fetch: wrapFetchWithTimeout(fetch, timeout),
    });
    this.namespace = namespace;
  }

  /**
   * Fetch all emails matching a given tag.
   */
  async getEmails(address: string): Promise<Email[]> {
    const response = await this.client.request(getEmailsQuery, {
      tag: this.getTagFromAddress(address),
      namespace: this.namespace,
    });
    return response.inbox.emails;
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
const getEmailsQuery = gql`
  query getEmails($namespace: String!, $tag: String!) {
    inbox(namespace: $namespace, tag: $tag, livequery: true) {
      result
      message
      emails {
        from
        subject
        text
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
        { field: subject, match: exact, action: include, value: $subject }
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
