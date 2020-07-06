/**
 * @file Custom Error classes. Useful as a way to see all potential errors that our system may throw/catch
 */

/**
 * A response returned a 403 status code, indicating an issue with the authorization of the request.
 * Examples of a ForbiddenError could be the user's browser prevented the session cookie from
 * being created, or the user hasn't consented to the data sharing agreement.
 */
export class ForbiddenError extends Error {
  constructor(...params) {
    super(...params);
    this.name = "ForbiddenError";
  }
}

/**
 * A fetch request failed due to a network error. The error wasn't the fault of the user,
 * and an issue was encountered while setting up or sending a request, or parsing the response.
 * Examples of a NetworkError could be the user's device lost internet connection, a CORS issue,
 * or a malformed request.
 */
export class NetworkError extends Error {
  constructor(...params) {
    super(...params);
    this.name = "NetworkError";
  }
}

/**
 * A transition between the current route state to the next route failed most likely because
 * a CONTINUE transition was not defined for the current route.
 */
export class RouteTransitionError extends Error {
  constructor(...params) {
    super(...params);
    this.name = "RouteTransitionError";
  }
}
