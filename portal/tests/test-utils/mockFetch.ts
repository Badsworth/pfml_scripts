/**
 * Intercept HTTP requests and return a mocked response. Only mocks the first fetch request,
 * using mockResolvedValueOnce!
 */
const mockFetch = ({
  response = { data: [] },
  status = 200,
}: {
  response?: { data?: unknown; errors?: unknown; warnings?: unknown };
  status?: number;
} = {}) => {
  global.fetch = jest.fn().mockResolvedValueOnce({
    json: jest.fn().mockResolvedValueOnce(response),
    ok: status < 300,
    status,
  });

  return global.fetch;
};

export default mockFetch;
