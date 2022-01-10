import { NrqlQuery } from "nr1";
import React from "react";
import { processTableRow } from "./services";

class MutiQuery extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      loading: true,
      queryPromises: this.props.nrqlQueries.map(() => ({
        loading: true,
      })),
    };
    this.queries = [];
    this.shouldFetch = true;
  }

  componentDidUpdate() {
    if (this.shouldFetch) {
      this.setState(
        {
          loading: true,
          queryPromises: this.props.nrqlQueries.map(() => ({
            loading: true,
          })),
        },
        () => {
          this.fetchLatestDataByQuery();
        }
      );
      this.shouldFetch = false;
      this.queries = this.props.nrqlQueries;
    }
  }

  shouldComponentUpdate(nextProps, nextState) {
    if (this.queries.length !== nextProps.nrqlQueries.length) {
      this.shouldFetch = true;
      return true;
    }
    for (let i = 0; i < nextProps.nrqlQueries.length; i++) {
      if (nextProps.nrqlQueries[i].query !== this.queries[i].query) {
        this.shouldFetch = true;
        return true;
      }
    }
    return nextState.queryPromises !== this.state.queryPromises;
  }

  fetchLatestDataByQuery = () => {
    const queryPromises = this.props.nrqlQueries.map((nrqlQuery) =>
      NrqlQuery.query(nrqlQuery).then((res) => {
        let data;
        if (nrqlQuery.formatType === NrqlQuery.FORMAT_TYPE.RAW) {
          data = res.data;
        } else {
          data = res.data.filter(
            (d) => !d.metadata.other_series && d.metadata.viz === "main"
          );
          if (data.length > 1) {
            data = data.map((row) => {
              return processTableRow(row);
            });
          } else {
            data = res.data[0];
          }
        }
        if (typeof nrqlQuery?.rowProcessor == "function") {
          if (data?.facets) {
            data.data = data.facets.map(nrqlQuery.rowProcessor);
          } else if (data?.length) {
            data = data.map(nrqlQuery.rowProcessor);
          } else {
            data.data = data.data.map(nrqlQuery.rowProcessor);
          }
        }

        if (typeof nrqlQuery?.postProcessor == "function") {
          data = nrqlQuery.postProcessor(data);
        }

        return data;
      })
    );

    return Promise.all(queryPromises).then((data) => {
      this.setState({
        queryPromises: data,
        loading: false,
      });
    });
  };

  render() {
    // if (this.state.queryPromises.length === 0) return null;
    return this.props.children(this.state.loading, this.state.queryPromises);
  }
}

export { MutiQuery };
