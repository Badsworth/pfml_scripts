import ConfirmationDialog from "../components/ConfirmationDialog";
import SlideOut from "../components/SlideOut";
import { Helmet } from "react-helmet-async";
import { useState } from "react";
import Button from "../components/Button";

export default function Maintenance() {
  const [showConfirmationDialog, setShowConfirmationDialog] = useState(false);
  const [showSlideOut, setShowSlideOut] = useState(false);

  const confirmationDialogCancelCallback = () => {
    setShowConfirmationDialog(false);
  };

  const confirmationDialogContinueCallback = () => {
    setShowConfirmationDialog(false);
  };

  const slideOutCloseCallback = () => {
    setShowSlideOut(false);
  };

  return (
    <>
      <Helmet>
        <title>Maintenance</title>
      </Helmet>
      <h1>Maintenance</h1>
      <p>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi ornare
        leo mi, nec lacinia nulla vestibulum eu. Maecenas consectetur lacus ut
        turpis tempor, in facilisis nisl posuere. Maecenas posuere dui nulla,
        non pulvinar ipsum auctor sit amet. Nulla facilisi. Class aptent taciti
        sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos.
        Praesent in venenatis libero. Maecenas sit amet accumsan lectus.
        Maecenas consequat tellus vitae sodales volutpat. Maecenas rhoncus augue
        eget diam hendrerit volutpat. Sed blandit vestibulum mauris, id
        porttitor nisl dictum sit amet. Praesent dignissim metus at volutpat
        facilisis. Praesent eu orci lacus. Nulla dictum, ex eu ornare dapibus,
        erat quam vestibulum ligula, in finibus ligula urna ac mi. Cras rutrum,
        magna non lacinia vulputate, lacus odio viverra ante, quis tempus sapien
        risus id odio.
      </p>
      <p>
        Proin ultrices sem risus, et convallis enim dictum in. Curabitur cursus,
        massa ac luctus vehicula, sapien ante porttitor nulla, in pretium erat
        libero in dolor. Integer et velit dapibus, convallis turpis vitae,
        cursus tortor. Vivamus aliquet, diam ullamcorper malesuada interdum,
        nunc neque scelerisque libero, vel condimentum tortor purus a tortor.
        Maecenas suscipit libero sit amet faucibus eleifend. Vestibulum ac orci
        luctus, eleifend neque egestas, tempus lectus. Phasellus at ante
        finibus, consectetur libero sollicitudin, sagittis lacus. Sed nec
        bibendum dui. Nam eget feugiat libero. Sed aliquet pulvinar cursus.
        Maecenas blandit nisl non lorem hendrerit placerat. Proin et ligula
        interdum, iaculis enim ut, lobortis enim.
      </p>
      <p>
        Aenean sed eros a felis feugiat congue non sed mi. Fusce fringilla
        lectus sed felis ornare, non posuere diam suscipit. Pellentesque
        habitant morbi tristique senectus et netus et malesuada fames ac turpis
        egestas. Nullam bibendum, metus vel sagittis ultricies, tellus lorem
        volutpat mauris, ac ullamcorper metus mauris eget lorem. Proin ut massa
        at felis accumsan sodales. Nullam suscipit bibendum augue, non feugiat
        neque rutrum sit amet. Integer rutrum viverra ex, sit amet ornare ligula
        vehicula sit amet. Aliquam blandit bibendum sem, nec ornare tortor
        scelerisque in. Nunc tristique felis vitae mollis elementum. Mauris ut
        quam id velit suscipit vehicula. Nulla facilisi. Aenean augue elit,
        suscipit non scelerisque vitae, laoreet in dolor. Donec ac ullamcorper
        arcu, sed condimentum eros. Aenean lacus turpis, iaculis eu felis ac,
        convallis consequat lacus.
      </p>
      <p>
        Ut hendrerit varius dictum. Aenean eget velit sollicitudin, vulputate
        metus nec, tristique dolor. Aliquam bibendum massa in leo rhoncus, sed
        iaculis risus varius. Cras sed neque in nulla suscipit blandit. Nunc id
        sem quis augue scelerisque malesuada. Pellentesque mauris nibh, varius
        in placerat a, tempor a nibh. Proin dictum ipsum volutpat gravida
        venenatis. Vestibulum placerat accumsan ultrices.
      </p>
      <p>
        Suspendisse lacus felis, convallis quis volutpat a, ultrices id neque.
        Proin sit amet tincidunt urna, convallis tempus risus. Curabitur mattis
        mollis est, non rhoncus neque sollicitudin sit amet. Mauris sit amet
        gravida arcu. In hac habitasse platea dictumst. Etiam elementum diam
        purus, ac lacinia magna lacinia rutrum. Pellentesque commodo sagittis
        tortor, id ornare eros tincidunt ut. Aliquam in purus risus. Nulla
        facilisi. Ut feugiat, leo et semper tempus, urna purus tristique ligula,
        eget molestie quam diam eget ante. Phasellus condimentum dignissim elit
        ac dictum. Nulla facilisi. Morbi nec lacus gravida, accumsan ante
        egestas, auctor tellus. Etiam ornare est accumsan pretium sollicitudin.
        Aenean in pretium velit.
      </p>
      <p>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi ornare
        leo mi, nec lacinia nulla vestibulum eu. Maecenas consectetur lacus ut
        turpis tempor, in facilisis nisl posuere. Maecenas posuere dui nulla,
        non pulvinar ipsum auctor sit amet. Nulla facilisi. Class aptent taciti
        sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos.
        Praesent in venenatis libero. Maecenas sit amet accumsan lectus.
        Maecenas consequat tellus vitae sodales volutpat. Maecenas rhoncus augue
        eget diam hendrerit volutpat. Sed blandit vestibulum mauris, id
        porttitor nisl dictum sit amet. Praesent dignissim metus at volutpat
        facilisis. Praesent eu orci lacus. Nulla dictum, ex eu ornare dapibus,
        erat quam vestibulum ligula, in finibus ligula urna ac mi. Cras rutrum,
        magna non lacinia vulputate, lacus odio viverra ante, quis tempus sapien
        risus id odio.
      </p>
      <p>
        Proin ultrices sem risus, et convallis enim dictum in. Curabitur cursus,
        massa ac luctus vehicula, sapien ante porttitor nulla, in pretium erat
        libero in dolor. Integer et velit dapibus, convallis turpis vitae,
        cursus tortor. Vivamus aliquet, diam ullamcorper malesuada interdum,
        nunc neque scelerisque libero, vel condimentum tortor purus a tortor.
        Maecenas suscipit libero sit amet faucibus eleifend. Vestibulum ac orci
        luctus, eleifend neque egestas, tempus lectus. Phasellus at ante
        finibus, consectetur libero sollicitudin, sagittis lacus. Sed nec
        bibendum dui. Nam eget feugiat libero. Sed aliquet pulvinar cursus.
        Maecenas blandit nisl non lorem hendrerit placerat. Proin et ligula
        interdum, iaculis enim ut, lobortis enim.
      </p>
      <p>
        Aenean sed eros a felis feugiat congue non sed mi. Fusce fringilla
        lectus sed felis ornare, non posuere diam suscipit. Pellentesque
        habitant morbi tristique senectus et netus et malesuada fames ac turpis
        egestas. Nullam bibendum, metus vel sagittis ultricies, tellus lorem
        volutpat mauris, ac ullamcorper metus mauris eget lorem. Proin ut massa
        at felis accumsan sodales. Nullam suscipit bibendum augue, non feugiat
        neque rutrum sit amet. Integer rutrum viverra ex, sit amet ornare ligula
        vehicula sit amet. Aliquam blandit bibendum sem, nec ornare tortor
        scelerisque in. Nunc tristique felis vitae mollis elementum. Mauris ut
        quam id velit suscipit vehicula. Nulla facilisi. Aenean augue elit,
        suscipit non scelerisque vitae, laoreet in dolor. Donec ac ullamcorper
        arcu, sed condimentum eros. Aenean lacus turpis, iaculis eu felis ac,
        convallis consequat lacus.
      </p>
      <p>
        Ut hendrerit varius dictum. Aenean eget velit sollicitudin, vulputate
        metus nec, tristique dolor. Aliquam bibendum massa in leo rhoncus, sed
        iaculis risus varius. Cras sed neque in nulla suscipit blandit. Nunc id
        sem quis augue scelerisque malesuada. Pellentesque mauris nibh, varius
        in placerat a, tempor a nibh. Proin dictum ipsum volutpat gravida
        venenatis. Vestibulum placerat accumsan ultrices.
      </p>
      <p>
        Suspendisse lacus felis, convallis quis volutpat a, ultrices id neque.
        Proin sit amet tincidunt urna, convallis tempus risus. Curabitur mattis
        mollis est, non rhoncus neque sollicitudin sit amet. Mauris sit amet
        gravida arcu. In hac habitasse platea dictumst. Etiam elementum diam
        purus, ac lacinia magna lacinia rutrum. Pellentesque commodo sagittis
        tortor, id ornare eros tincidunt ut. Aliquam in purus risus. Nulla
        facilisi. Ut feugiat, leo et semper tempus, urna purus tristique ligula,
        eget molestie quam diam eget ante. Phasellus condimentum dignissim elit
        ac dictum. Nulla facilisi. Morbi nec lacus gravida, accumsan ante
        egestas, auctor tellus. Etiam ornare est accumsan pretium sollicitudin.
        Aenean in pretium velit.
      </p>
      <p>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi ornare
        leo mi, nec lacinia nulla vestibulum eu. Maecenas consectetur lacus ut
        turpis tempor, in facilisis nisl posuere. Maecenas posuere dui nulla,
        non pulvinar ipsum auctor sit amet. Nulla facilisi. Class aptent taciti
        sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos.
        Praesent in venenatis libero. Maecenas sit amet accumsan lectus.
        Maecenas consequat tellus vitae sodales volutpat. Maecenas rhoncus augue
        eget diam hendrerit volutpat. Sed blandit vestibulum mauris, id
        porttitor nisl dictum sit amet. Praesent dignissim metus at volutpat
        facilisis. Praesent eu orci lacus. Nulla dictum, ex eu ornare dapibus,
        erat quam vestibulum ligula, in finibus ligula urna ac mi. Cras rutrum,
        magna non lacinia vulputate, lacus odio viverra ante, quis tempus sapien
        risus id odio.
      </p>
      <p>
        Proin ultrices sem risus, et convallis enim dictum in. Curabitur cursus,
        massa ac luctus vehicula, sapien ante porttitor nulla, in pretium erat
        libero in dolor. Integer et velit dapibus, convallis turpis vitae,
        cursus tortor. Vivamus aliquet, diam ullamcorper malesuada interdum,
        nunc neque scelerisque libero, vel condimentum tortor purus a tortor.
        Maecenas suscipit libero sit amet faucibus eleifend. Vestibulum ac orci
        luctus, eleifend neque egestas, tempus lectus. Phasellus at ante
        finibus, consectetur libero sollicitudin, sagittis lacus. Sed nec
        bibendum dui. Nam eget feugiat libero. Sed aliquet pulvinar cursus.
        Maecenas blandit nisl non lorem hendrerit placerat. Proin et ligula
        interdum, iaculis enim ut, lobortis enim.
      </p>
      <p>
        Aenean sed eros a felis feugiat congue non sed mi. Fusce fringilla
        lectus sed felis ornare, non posuere diam suscipit. Pellentesque
        habitant morbi tristique senectus et netus et malesuada fames ac turpis
        egestas. Nullam bibendum, metus vel sagittis ultricies, tellus lorem
        volutpat mauris, ac ullamcorper metus mauris eget lorem. Proin ut massa
        at felis accumsan sodales. Nullam suscipit bibendum augue, non feugiat
        neque rutrum sit amet. Integer rutrum viverra ex, sit amet ornare ligula
        vehicula sit amet. Aliquam blandit bibendum sem, nec ornare tortor
        scelerisque in. Nunc tristique felis vitae mollis elementum. Mauris ut
        quam id velit suscipit vehicula. Nulla facilisi. Aenean augue elit,
        suscipit non scelerisque vitae, laoreet in dolor. Donec ac ullamcorper
        arcu, sed condimentum eros. Aenean lacus turpis, iaculis eu felis ac,
        convallis consequat lacus.
      </p>
      <p>
        Ut hendrerit varius dictum. Aenean eget velit sollicitudin, vulputate
        metus nec, tristique dolor. Aliquam bibendum massa in leo rhoncus, sed
        iaculis risus varius. Cras sed neque in nulla suscipit blandit. Nunc id
        sem quis augue scelerisque malesuada. Pellentesque mauris nibh, varius
        in placerat a, tempor a nibh. Proin dictum ipsum volutpat gravida
        venenatis. Vestibulum placerat accumsan ultrices.
      </p>
      <p>
        Suspendisse lacus felis, convallis quis volutpat a, ultrices id neque.
        Proin sit amet tincidunt urna, convallis tempus risus. Curabitur mattis
        mollis est, non rhoncus neque sollicitudin sit amet. Mauris sit amet
        gravida arcu. In hac habitasse platea dictumst. Etiam elementum diam
        purus, ac lacinia magna lacinia rutrum. Pellentesque commodo sagittis
        tortor, id ornare eros tincidunt ut. Aliquam in purus risus. Nulla
        facilisi. Ut feugiat, leo et semper tempus, urna purus tristique ligula,
        eget molestie quam diam eget ante. Phasellus condimentum dignissim elit
        ac dictum. Nulla facilisi. Morbi nec lacus gravida, accumsan ante
        egestas, auctor tellus. Etiam ornare est accumsan pretium sollicitudin.
        Aenean in pretium velit.
      </p>
      <p>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi ornare
        leo mi, nec lacinia nulla vestibulum eu. Maecenas consectetur lacus ut
        turpis tempor, in facilisis nisl posuere. Maecenas posuere dui nulla,
        non pulvinar ipsum auctor sit amet. Nulla facilisi. Class aptent taciti
        sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos.
        Praesent in venenatis libero. Maecenas sit amet accumsan lectus.
        Maecenas consequat tellus vitae sodales volutpat. Maecenas rhoncus augue
        eget diam hendrerit volutpat. Sed blandit vestibulum mauris, id
        porttitor nisl dictum sit amet. Praesent dignissim metus at volutpat
        facilisis. Praesent eu orci lacus. Nulla dictum, ex eu ornare dapibus,
        erat quam vestibulum ligula, in finibus ligula urna ac mi. Cras rutrum,
        magna non lacinia vulputate, lacus odio viverra ante, quis tempus sapien
        risus id odio.
      </p>
      <p>
        Proin ultrices sem risus, et convallis enim dictum in. Curabitur cursus,
        massa ac luctus vehicula, sapien ante porttitor nulla, in pretium erat
        libero in dolor. Integer et velit dapibus, convallis turpis vitae,
        cursus tortor. Vivamus aliquet, diam ullamcorper malesuada interdum,
        nunc neque scelerisque libero, vel condimentum tortor purus a tortor.
        Maecenas suscipit libero sit amet faucibus eleifend. Vestibulum ac orci
        luctus, eleifend neque egestas, tempus lectus. Phasellus at ante
        finibus, consectetur libero sollicitudin, sagittis lacus. Sed nec
        bibendum dui. Nam eget feugiat libero. Sed aliquet pulvinar cursus.
        Maecenas blandit nisl non lorem hendrerit placerat. Proin et ligula
        interdum, iaculis enim ut, lobortis enim.
      </p>
      <p>
        Aenean sed eros a felis feugiat congue non sed mi. Fusce fringilla
        lectus sed felis ornare, non posuere diam suscipit. Pellentesque
        habitant morbi tristique senectus et netus et malesuada fames ac turpis
        egestas. Nullam bibendum, metus vel sagittis ultricies, tellus lorem
        volutpat mauris, ac ullamcorper metus mauris eget lorem. Proin ut massa
        at felis accumsan sodales. Nullam suscipit bibendum augue, non feugiat
        neque rutrum sit amet. Integer rutrum viverra ex, sit amet ornare ligula
        vehicula sit amet. Aliquam blandit bibendum sem, nec ornare tortor
        scelerisque in. Nunc tristique felis vitae mollis elementum. Mauris ut
        quam id velit suscipit vehicula. Nulla facilisi. Aenean augue elit,
        suscipit non scelerisque vitae, laoreet in dolor. Donec ac ullamcorper
        arcu, sed condimentum eros. Aenean lacus turpis, iaculis eu felis ac,
        convallis consequat lacus.
      </p>
      <p>
        Ut hendrerit varius dictum. Aenean eget velit sollicitudin, vulputate
        metus nec, tristique dolor. Aliquam bibendum massa in leo rhoncus, sed
        iaculis risus varius. Cras sed neque in nulla suscipit blandit. Nunc id
        sem quis augue scelerisque malesuada. Pellentesque mauris nibh, varius
        in placerat a, tempor a nibh. Proin dictum ipsum volutpat gravida
        venenatis. Vestibulum placerat accumsan ultrices.
      </p>
      <p>
        Suspendisse lacus felis, convallis quis volutpat a, ultrices id neque.
        Proin sit amet tincidunt urna, convallis tempus risus. Curabitur mattis
        mollis est, non rhoncus neque sollicitudin sit amet. Mauris sit amet
        gravida arcu. In hac habitasse platea dictumst. Etiam elementum diam
        purus, ac lacinia magna lacinia rutrum. Pellentesque commodo sagittis
        tortor, id ornare eros tincidunt ut. Aliquam in purus risus. Nulla
        facilisi. Ut feugiat, leo et semper tempus, urna purus tristique ligula,
        eget molestie quam diam eget ante. Phasellus condimentum dignissim elit
        ac dictum. Nulla facilisi. Morbi nec lacus gravida, accumsan ante
        egestas, auctor tellus. Etiam ornare est accumsan pretium sollicitudin.
        Aenean in pretium velit.
      </p>
    </>
  );
}
