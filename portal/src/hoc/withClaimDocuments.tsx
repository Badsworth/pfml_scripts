import {
  BenefitsApplicationDocument,
  filterByApplication,
} from "../models/Document";
import React, { useEffect } from "react";
import withUser, { WithUserProps } from "./withUser";
import BenefitsApplication from "../models/BenefitsApplication";
import PageNotFound from "../components/PageNotFound";
import assert from "assert";

export interface QueryForWithClaimDocuments {
  claim_id?: string;
}

export interface WithClaimDocumentsProps extends WithUserProps {
  isLoadingDocuments: boolean;
  documents: BenefitsApplicationDocument[];
}

/**
 * Higher order component that loads documents based on query parameters if they are not yet loaded
 */
function withClaimDocuments<
  T extends WithClaimDocumentsProps & { claim?: BenefitsApplication }
>(Component: React.ComponentType<T>) {
  const ComponentWithDocuments = (
    props: Omit<T, "documents" | "isLoadingDocuments"> & {
      query: QueryForWithClaimDocuments;
    }
  ) => {
    const { appLogic, claim, query } = props;
    const {
      documents: { loadAll, documents, hasLoadedClaimDocuments },
      users,
    } = appLogic;

    // TODO (CP-2589): Clean up once application flow uses the same document upload components
    const application_id = claim ? claim.application_id : query.claim_id;

    const shouldLoad = !!(
      application_id && !hasLoadedClaimDocuments(application_id)
    );
    assert(documents);
    // Since we are within a withUser higher order component, user should always be set
    assert(users.user);

    useEffect(() => {
      if (shouldLoad) {
        loadAll(application_id);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [shouldLoad]);

    if (!application_id) {
      return <PageNotFound />;
    }

    return (
      <Component
        {...(props as T & { query: QueryForWithClaimDocuments })}
        documents={filterByApplication(documents.items, application_id)}
        isLoadingDocuments={shouldLoad}
      />
    );
  };

  return withUser(ComponentWithDocuments);
}

export default withClaimDocuments;
