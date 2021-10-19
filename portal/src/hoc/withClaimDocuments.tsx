import React, { useEffect } from "react";
import DocumentCollection from "../models/DocumentCollection";
import User from "../models/User";
import assert from "assert";
import withUser from "./withUser";

interface ComponentWithDocumentsProps {
  appLogic: {
    users: {
      user: User;
    };
    documents: {
      hasLoadedClaimDocuments: (application_id: string) => boolean;
      documents: DocumentCollection;
      loadAll: (application_id: string) => void;
    };
  };
  claim: {
    application_id: string;
  };
  query: {
    claim_id: string;
  };
}

/**
 * Higher order component that loads documents based on query parameters if they are not yet loaded
 * @param {React.Component} Component - Component to receive documents prop
 * @returns {React.Component} - Component with documents prop
 */
const withClaimDocuments = (Component) => {
  const ComponentWithDocuments = (props: ComponentWithDocumentsProps) => {
    const { appLogic, claim, query } = props;
    const {
      documents: { loadAll, documents, hasLoadedClaimDocuments },
      users,
    } = appLogic;

    // TODO (CP-2589): Clean up once application flow uses the same document upload components
    const application_id = claim ? claim.application_id : query.claim_id;

    const shouldLoad = !hasLoadedClaimDocuments(application_id);
    assert(documents);
    // Since we are within a withUser higher order component, user should always be set
    assert(users.user);

    useEffect(() => {
      if (shouldLoad) {
        loadAll(application_id);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [shouldLoad]);

    return (
      <Component
        {...props}
        documents={documents.filterByApplication(application_id)}
        isLoadingDocuments={shouldLoad}
      />
    );
  };

  return withUser(ComponentWithDocuments);
};

export default withClaimDocuments;
