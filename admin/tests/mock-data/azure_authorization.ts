type AuthMockData = {
  user: User;
  sso_access_tokens: SsoAccessTokens;
  sso_auth_uri: SsoAuthUri;
  sso_code_response: SsoCodeResponse;
  post_login_redirect: string;
  post_logout_redirect: string;
};

type User = {
  sub_id: string;
  first_name: string;
  last_name: string;
  email_address: string;
  groups: string[];
};

type SsoAccessTokens = {
  access_token?: string;
  id_token: string;
  refresh_token: string;
};

type SsoAuthUri = {
  auth_uri?: string;
  claims_challenge: string | null;
  code_verifier: string;
  nonce: string;
  redirect_uri: string;
  scope: string[];
  state: string;
};

type SsoCodeResponse = {
  code: string;
  state: string;
  session_state: string;
};

const authMockData: AuthMockData = {
  user: {
    sub_id: "z9y8x7w6",
    first_name: "John",
    last_name: "Doe",
    email_address: "test@email.com",
    groups: [],
  },
  sso_access_tokens: {
    access_token: "a1b2c3",
    id_token: "d4e5f6",
    refresh_token: "g7h8i9",
  },
  sso_auth_uri: {
    auth_uri: "https://login.example.com",
    claims_challenge: null,
    code_verifier: "j10k11l12",
    nonce: "mnop",
    redirect_uri: "http://localhost:3000",
    scope: ["profile", "u13v14w15", "openid", "offline_access"],
    state: "qrst",
  },
  sso_code_response: {
    code: "0.abc123zyx987",
    state: "4d3c2b1a",
    session_state: "z9y8x7w6",
  },
  post_login_redirect: "/settings",
  post_logout_redirect: "http://localhost:3000/?logged_out=true",
};

export default authMockData;
