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
      line1: `To activate your account, you need to verify your email address. <a href="https://${process.env.PORTAL_DOMAIN}/verify-account" rel="noopener" target="_blank">Return to the application</a> and enter this 6-digit code:`,
      line2: "This code is only valid for 24 hours.",
      subject: "Verify your Paid Family and Medical Leave account",
    };
  } else if (messageType === "CustomMessage_ForgotPassword") {
    messageStrings = {
      line1: `We received a request to reset your Paid Family and Medical Leave account password. <a href="https://${process.env.PORTAL_DOMAIN}/reset-password" rel="noopener" target="_blank">Return to the application</a> and enter this 6-digit code:`,
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
      <table width="100%" style="font-family: Open Sans,Helvetica
      Neue,Helvetica,Arial,sans-serif;
      font-size: 16px;
      text-align: left;"
      cellpadding="0"
      cellspacing="0">
      <tbody>
          <tr>
              <td style="background: #14558f; height: 24px"></td>
          </tr>
          <tr>
              <td
                  style="background: #be5817;
                  padding: 16px 32px;">
                  <table
                      align="center"
                      cellspacing="0"
                      style="max-width: 600px;"
                      width="100%">
                      <tbody>
                          <tr>
                              <td>
                                  <img
                                      alt="Massachusetts Paid Family and Medical Leave"
                                      src="https://mcusercontent.com/0757f7959581770082e8f2fd9/images/4665cf36-af48-4bce-9032-33a7786052de.png"
                                      width="264"
                                      style="padding-bottom: 0;"
                                      class="mcnImage"
                                      />
                              </td>
                          </tr>
                      </tbody>
                  </table>
              </td>
          </tr>
          <tr>
              <td>
                  <table
                      align="center"
                      style="line-height: 150%;
                      text-align: left;
                      max-width: 600px;
                      color:#535353;padding-bottom: 32px;" width="100%">
                      <tbody>
                      <tr>
                      <td style="padding: 32px;">
                        ${messageStrings.line1}
                      </td>
                    </tr>
            
                    <tr>
                      <td style="text-align: center">
                        <strong style="display: inline-block; font-size: 22px;">${codeParam}</strong>
                      </td>
                    </tr>
            
                    <tr>
                      <td style="padding: 32px; text-align: center;">
                        ${messageStrings.line2}
                      </td>
                    </tr>
                      </tbody>
                  </table>
              </td>
          </tr>
          <tr>
              <td style="background: #FAFAFA; border-top: 3px solid
                  #EAEAEA;">
                  <table
                      align="center"
                      style="max-width: 600px;"
                      width="100%">
                      <tbody>
                          <tr>
                              <td>
                                  <img
                                      align="center"
                                      alt=""
                                      src="https://mcusercontent.com/0757f7959581770082e8f2fd9/images/a163a15d-9150-4959-9b02-998caa00bca4.png"
                                      width="564"
                                      style="max-width: 903px;
                                      padding: 0 18px;
                                      display: inline;
                                      vertical-align: bottom;" />
                              </td>
                          </tr>

                          <tr>
                              <td style="padding:0px 18px 9px;
                                  text-align: left;
                                  color: #656565; font-size: 12px;">
                                  <div>
                                      <a
                                          href="https://www.mass.gov/orgs/department-of-family-and-medical-leave"
                                          rel="noopener"
                                          target="_blank"
                                          data-saferedirecturl="https://www.google.com/url?hl=en&amp;q=https://www.mass.gov/orgs/department-of-family-and-medical-leave&amp;source=gmail&amp;ust=1607720450081000&amp;usg=AFQjCNF21ULm-5y7N8G5cZXEVu-uHldNPg">
                                          Department of Family &
                                          Medical Leave
                                      </a>
                                  </div>
                                  <div>P.O. Box 838, Lawrence, MA
                                      01842</div>
                                  <div>(833) 344-7365 from 8am–5pm ET</div>
                              </td>
                          </tr>

                          <tr>
                              <td style="font-size: 12px;
                                  font-style: italic; padding: 18px;">
                                  This e-mail message is for the sole
                                  use of the intended recipient and
                                  may contain confidential and
                                  privileged information. Any
                                  unauthorized review, use,
                                  disclosure, or distribution is
                                  strictly prohibited. If you are not
                                  the intended recipient, please
                                  contact us at (833) 344-7365 from
                                  8am–5pm ET and then destroy all
                                  copies of the original message.
                              </td>
                          </tr>
                      </tbody>
                  </table>
              </td>
          </tr>
      </tbody>
    </table>
  `;
}
