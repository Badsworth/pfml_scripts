using System.Collections.Generic;

namespace PfmlPdfApi.Common
{
    public class ResponseMessage<T>
    {
        // private members
        private T _messageBody;

        // public constructors
        /// <summary>
        /// Create a new response payload with a message body domain object.
        /// </summary>
        /// <param name="messageBody"></param>
        public ResponseMessage(T messageBody)
        {
            _messageBody = messageBody;
        }

        // public attributes
        /// <summary>
        /// Returns the status of the request represented by this message.  The value defaults to success.
        /// </summary>
        public string Status { get; set; } = MessageConstants.MsgStatusSuccess;

        /// <summary>
        /// Returns the domain object that represents the body of the response.
        /// </summary>
        public T Payload
        {
            get
            {
                return _messageBody;
            }
            set
            {
                _messageBody = value;

            }
        }

        public string ErrorMessage {get; set;}
    }
}