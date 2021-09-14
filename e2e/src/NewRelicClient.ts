import { gql, GraphQLClient } from "graphql-request";

type QueryResult<T = unknown> = {
  actor: {
    account: {
      nrql: {
        results: T[];
      };
    };
  };
};

// @todo: It would be nice to type this more strongly, but it doesn't feel worth it.
type Dashboard = Record<string, unknown>;

export default class NewRelicClient {
  client: GraphQLClient;
  constructor(private apiKey: string, private accountId: number) {
    this.client = new GraphQLClient(`https://api.newrelic.com/graphql`, {
      headers: {
        "Content-Type": "application/json",
        "API-Key": this.apiKey,
      },
    });
  }
  async nrql<R = unknown>(nrql: string): Promise<R[]> {
    const query = gql`
      query getNRQLResult($accountId: Int!, $nrql: NRQL!) {
        actor {
          account(id: $accountId) {
            nrql(query: $nrql) {
              results
            }
          }
        }
      }
    `;

    return this.client
      .request<QueryResult<R>>(query, {
        accountId: this.accountId,
        nrql,
      })
      .then((result) => result.actor.account.nrql.results);
  }

  async getEntityGuid(entityQuery: string): Promise<string | undefined> {
    type EntityGuidResult = {
      actor: {
        entitySearch: {
          results: {
            entities: {
              guid: string;
            }[];
          };
        };
      };
    };
    const query = gql`
      query getEntityGuid($entityQuery: String!) {
        actor {
          entitySearch(query: $entityQuery) {
            results {
              entities {
                guid
              }
            }
          }
        }
      }
    `;
    return this.client
      .request<EntityGuidResult>(query, { entityQuery })
      .then((result) => {
        if (result.actor.entitySearch.results.entities.length > 1) {
          throw new Error(`Invalid number of entities returned for query`);
        }
        return result.actor.entitySearch.results.entities
          .map((r) => r.guid)
          .pop();
      });
  }

  async createDashboard(dashboard: Dashboard): Promise<void> {
    const query = gql`
      mutation CreateDashboard($accountId: Int!, $dashboard: DashboardInput!) {
        dashboardCreate(accountId: $accountId, dashboard: $dashboard) {
          entityResult {
            guid
          }
          errors {
            description
            type
          }
        }
      }
    `;
    await this.client.request(query, { dashboard, accountId: this.accountId });
  }

  async updateDashboard(guid: string, dashboard: Dashboard): Promise<void> {
    const query = gql`
      mutation UpdateDashboard(
        $guid: EntityGuid!
        $dashboard: DashboardInput!
      ) {
        dashboardUpdate(guid: $guid, dashboard: $dashboard) {
          entityResult {
            guid
          }
          errors {
            description
            type
          }
        }
      }
    `;
    await this.client.request(query, { dashboard, guid });
  }
  async upsertDashboardByName(
    dashboard: Dashboard
  ): Promise<"CREATED" | "UPDATED"> {
    const guid = await this.getEntityGuid(
      `name = '${dashboard.name}' AND type IN ('DASHBOARD')`
    );
    if (guid) {
      await this.updateDashboard(guid, dashboard);
      return "UPDATED";
    } else {
      await this.createDashboard(dashboard);
      return "CREATED";
    }
  }
}
