import { processRawNRQLDataAsTable } from "../services";
import { NrqlQuery, Spinner, SectionMessage } from "nr1";
import React from "react";

export class E2EQuery extends React.Component {
  state = {
    /**
     * @type BaseDAOV2
     */
    DAO: {},
  };

  static getDerivedStateFromProps(props) {
    return {
      /**
       * @type BaseDAOV2
       */
      DAO: props.DAO,
    };
  }

  constructor(props) {
    super(props);
    this.children = props.children;
  }

  render() {
    return (
      <NrqlQuery
        query={this.state.DAO.query()}
        accountId={this.state.DAO.accountId}
        formatType={this.state.DAO.FORMAT_TYPE}
      >
        {({ data, loading, error }) => {
          if (loading) {
            return <Spinner />;
          }
          if (
            error &&
            error?.message !==
              "No events found -- do you have the correct event type and time range?"
          ) {
            return (
              <SectionMessage
                title={"There was an error executing the query"}
                description={error.message}
                type={SectionMessage.TYPE.CRITICAL}
              />
            );
          }
          if (
            data === null ||
            error?.message ===
              "No events found -- do you have the correct event type and time range?"
          ) {
            return (
              <SectionMessage
                title={"No Data"}
                type={SectionMessage.TYPE.INFO}
              />
            );
          }

          if (this.state.DAO.FORMAT_TYPE === NrqlQuery.FORMAT_TYPE.RAW) {
            data = processRawNRQLDataAsTable(data);
          }
          if (typeof this.state.DAO.rowProcessor == "function") {
            data = data.map((datum) => {
              return this.state.DAO.rowProcessor(datum);
            });
          }
          if (typeof this.state.DAO.postProcessor == "function") {
            data = this.state.DAO.postProcessor(data);
          }
          return this.children({ data: data });
        }}
      </NrqlQuery>
    );
  }
}
