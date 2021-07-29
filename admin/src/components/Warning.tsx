type Props = {
  message: string;
};

export default function Warning({ message }: Props) {
  return (
    <div className="warning">
      <i className="pfml-icon--alert-2 warning__icon"></i>

      <span>{message}</span>
    </div>
  );
}
