import { ComponentType, ComponentProps, useState } from "react";

type CommonProps = {
  isOpen: boolean;
  onClose: Function;
  onOpen: Function;
};

export default function usePopup<T extends ComponentType<any>>(
  props: ComponentProps<T>,
): CommonProps & ComponentProps<T> {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const onMouseEvent =
    (callback: Function, endState: boolean) => (event: MouseEvent) => {
      event.preventDefault();
      if (callback) callback(event);
      setIsOpen(endState);
    };
  const onClose = onMouseEvent(props.onClose, false);
  const onOpen = onMouseEvent(props.onOpen, true);

  return { ...props, isOpen, onOpen, onClose };
}
