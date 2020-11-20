/**
 * Lambda function used for customizing a subset of Cognito Email and SMS messages
 * @param {object} event
 * @param {string} event.triggerSource - the type of message
 * @param {object} event.request
 * @param {string} event.request.codeParameter - message template placeholder for the code that will be sent
 * @param {*} _context - not used
 * @param {Function} callback - we need to call this with the mutated event
 */
exports.handler = (event, _context, callback) => {
  const messageType = event.triggerSource;
  const codeParam = event.request.codeParameter;
  let messageStrings;

  // SignUp and ResendCode are related to the same action: verifying a new account
  if (
    messageType === "CustomMessage_SignUp" ||
    messageType === "CustomMessage_ResendCode"
  ) {
    messageStrings = {
      line1:
        "To activate your account, you need to verify your email address. Return to the application and enter this 6-digit code:",
      line2: "This code is only valid for 24 hours.",
      subject: "Verify your Paid Family and Medical Leave account",
    };
  } else if (messageType === "CustomMessage_ForgotPassword") {
    messageStrings = {
      line1:
        "We received a request to reset your Paid Family and Medical Leave account password. Return to the application and enter this 6-digit code:",
      line2:
        "This code is only valid for 24 hours. If you didn’t request a password reset, please ignore this email. Your password won’t be changed.",
      subject: "Reset your Paid Family and Medical Leave password",
    };
  }

  if (messageStrings) {
    event.response.emailMessage = generateVerificationEmail(
      messageStrings,
      codeParam
    );
    event.response.emailSubject = messageStrings.subject;
  }

  callback(null, event);
};

/**
 * Verification emails include a code a user needs to enter on the website.
 * @param {object} messageStrings
 * @param {string} codeParam - message template placeholder for the code that will be sent
 * @returns {string}
 */
function generateVerificationEmail(messageStrings, codeParam) {
  /*
    Design tokens
    ============================
    Blue: #14558F
    Green: #388557
    Gray background: #F2F2F2
    Gray text: #535353
    Large text: 22px
    Body text: 16px
    Small text: 12px
  */
  return `
    <table align="center" cellspacing="0" style="font-family: Helvetica, Arial, sans-serif; font-size: 16px; text-align: left; max-width: 800px;" width="100%">
      <tbody>
        <tr>
          <td style="background: #388557; height: 24px;"></td>
        </tr>
        <tr>
          <td style="background: #14558F; color: #fff; font-size: 22px; font-weight: bold; padding: 16px 32px;">
            Department of Family and Medical Leave
          </td>
        </tr>
        <tr>
          <td style="padding: 32px;">
            ${messageStrings.line1}
          </td>
        </tr>

        <tr>
          <td style="text-align: center">
            <strong style="background: #14558F; color: #fff; display: inline-block; font-size: 22px; padding: 16px 32px;">${codeParam}</strong>
          </td>
        </tr>

        <tr>
          <td style="padding: 32px; text-align: center;">
            ${messageStrings.line2}
          </td>
        </tr>

        <tr>
          <td style="background: #F2F2F2; color: #535353; font-size: 12px; font-style: italic; padding: 32px;">
            This is an automatically generated message from Commonwealth of Massachusetts
            <a href="https://www.mass.gov/orgs/department-of-family-and-medical-leave">Department of Family and Medical Leave</a>.
            Replies are not monitored or answered.
          </td>
        </tr>
      </tbody>
  </table>`;
}
