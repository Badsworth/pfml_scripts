/**
 * @file Custom Error classes. Useful as a way to see all potential errors that our system may throw/catch
 */

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
