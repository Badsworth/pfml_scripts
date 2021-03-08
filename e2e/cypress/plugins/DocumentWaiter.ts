import { getApplicationsByApplication_idDocuments } from "../../src/api";
import AuthenticationManager from "../../src/submission/AuthenticationManager";
import pRetry from "p-retry";

type WaitForDocumentOpts = {
  credentials: Credentials;
  application_id: string;
  document_type: string;
};

export default class DocumentWaiter {
  constructor(
    private apiBaseUrl: string,
    private authenticator: AuthenticationManager
  ) {}

  async waitForClaimDocuments({
    credentials,
    application_id,
    document_type,
  }: WaitForDocumentOpts): Promise<boolean> {
    const session = await this.authenticator.authenticate(
      credentials.username,
      credentials.password
    );
    const opts = {
      baseUrl: this.apiBaseUrl,
      headers: {
        Authorization: `Bearer ${session.getAccessToken().getJwtToken()}`,
        "User-Agent": "PFML Cypress Testing",
      },
    };
    // Retry the document request indefinitely (Cypress task will time out to stop).
    return pRetry(
      async () => {
        const documents = await getApplicationsByApplication_idDocuments(
          { application_id },
          opts
        );
        const discoveredTypes = (documents.data.data ?? []).map(
          (doc) => doc.document_type as string
        );
        if (!discoveredTypes.includes(document_type)) {
          throw new Error(
            `Detected no documents of type ${document_type}. Instead, we found: ${discoveredTypes.join(
              ","
            )}`
          );
        }
        return true;
      },
      { forever: true, maxTimeout: 10000 }
    );
  }
}
