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
    const {
      appLogic,
      claim: { application_id },
    } = props;
    const {
      documents: { loadAll, documents, hasLoadedClaimDocuments },
      users,
    } = appLogic;

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

  ComponentWithDocuments.propTypes = {
    appLogic: PropTypes.shape({
      users: PropTypes.shape({
        user: PropTypes.instanceOf(User).isRequired,
      }).isRequired,
      documents: PropTypes.shape({
        hasLoadedClaimDocuments: PropTypes.func.isRequired,
        documents: PropTypes.instanceOf(DocumentCollection).isRequired,
        loadAll: PropTypes.func.isRequired,
      }).isRequired,
      appErrors: PropTypes.object.isRequired,
    }).isRequired,
    claim: PropTypes.shape({
      application_id: PropTypes.string.isRequired,
    }),
  };

  return withUser(ComponentWithDocuments);
};

export default withClaimDocuments;
