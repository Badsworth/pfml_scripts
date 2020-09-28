import React, { useEffect } from "react";
import DocumentCollection from "../models/DocumentCollection";
import PropTypes from "prop-types";
import User from "../models/User";
import assert from "assert";
import withUser from "./withUser";

/**
 * Higher order component that loads documents based on query parameters if they are not yet loaded
 * @param {React.Component} Component - Component to receive documents prop
 * @returns {React.Component} - Component with documents prop
 */
const withClaimDocuments = (Component) => {
  const ComponentWithDocuments = (props) => {
    const { appLogic, query } = props;
    const {
      documents: { load, documents, hasLoadedClaimDocuments },
      users,
    } = appLogic;
    const shouldLoad = !hasLoadedClaimDocuments(query.claim_id);

    assert(documents);
    // Since we are within a withUser higher order component, user should always be set
    assert(users.user);

    useEffect(() => {
      if (appLogic.appErrors.isEmpty && shouldLoad) {
        load(query.claim_id);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [appLogic.appErrors.isEmpty]);

    return (
      <Component
        {...props}
        documents={documents.filterByApplication(query.claim_id)}
        isDocumentLoading={shouldLoad}
      />
    );
  };

  ComponentWithDocuments.propTypes = {
    appLogic: PropTypes.shape({
      users: PropTypes.shape({
        user: PropTypes.instanceOf(User).isRequired,
      }).isRequired,
      documents: PropTypes.shape({
        hasLoadedClaimDocuments: PropTypes.func.isRequired,
        documents: PropTypes.instanceOf(DocumentCollection).isRequired,
        load: PropTypes.func.isRequired,
      }).isRequired,
      appErrors: PropTypes.object.isRequired,
    }).isRequired,
    query: PropTypes.shape({
      claim_id: PropTypes.string.isRequired,
    }).isRequired,
  };

  return withUser(ComponentWithDocuments);
};

export default withClaimDocuments;
