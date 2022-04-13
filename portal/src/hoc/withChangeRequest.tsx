import withChangeRequests, {
  WithChangeRequestsProps,
} from "./withChangeRequests";
import ChangeRequest from "../models/ChangeRequest";
import PageNotFound from "../components/PageNotFound";
import React from "react";

interface WithChangeRequestProps
  extends Omit<WithChangeRequestsProps, "query"> {
  change_request: ChangeRequest;
}

interface QueryForWithChangeRequest {
  query: {
    change_request_id?: string;
  };
}

function withChangeRequest<T extends WithChangeRequestProps>(
  Component: React.ComponentType<T>
) {
  const ComponentWithChangeRequest = (
    props: WithChangeRequestsProps & QueryForWithChangeRequest
  ) => {
    const change_request_id = props.query.change_request_id;
    const changeRequest = props.change_requests.getItem(
      change_request_id || ""
    );

    if (!change_request_id || !changeRequest) {
      return <PageNotFound />;
    }

    return (
      <Component
        {...(props as T & QueryForWithChangeRequest)}
        change_request={changeRequest}
      />
    );
  };
  return withChangeRequests(ComponentWithChangeRequest);
}

export default withChangeRequest;
