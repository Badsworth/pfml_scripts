#
# Regenerate payments files - main entry points.
#

from typing import Type

import massgov.pfml.db
import massgov.pfml.util.logging
from massgov.pfml.db.models.employees import CtrBatchIdentifier, ReferenceFile, ReferenceFileType

from . import base, gax, vcc

logger = massgov.pfml.util.logging.get_logger(__name__)


def regenerate_batch(
    batch_id: str, ctr_outbound_path: str, db_session: massgov.pfml.db.Session
) -> None:
    """Regenerate a VCC or GAX for the given Batch ID."""
    reference_file = reference_file_by_ctr_batch(batch_id, db_session)

    regenerator_class = regenerator_class_for_reference_file(reference_file)
    regenerator = regenerator_class(reference_file, ctr_outbound_path, db_session)

    regenerator.run()


def reference_file_by_ctr_batch(
    batch_id: str, db_session: massgov.pfml.db.Session
) -> ReferenceFile:
    """Read a ReferenceFile from the database for the given Batch ID."""
    reference_file: ReferenceFile = (
        db_session.query(ReferenceFile)
        .join(CtrBatchIdentifier)
        .filter(CtrBatchIdentifier.ctr_batch_identifier == batch_id)
        .one_or_none()
    )
    if reference_file is None:
        raise RuntimeError("batch %s not found in database" % batch_id)

    logger.info(
        "batch %s: reference_file %s, type %s",
        batch_id,
        reference_file.file_location,
        reference_file.reference_file_type.reference_file_type_description,
    )

    return reference_file


def regenerator_class_for_reference_file(
    reference_file: ReferenceFile,
) -> Type[base.ReferenceFileRegenerator]:
    """Determine the concrete class that can regenerate the given ReferenceFile."""
    if reference_file.reference_file_type_id == ReferenceFileType.VCC.reference_file_type_id:
        return vcc.RegeneratorVCC
    elif reference_file.reference_file_type_id == ReferenceFileType.GAX.reference_file_type_id:
        return gax.RegeneratorGAX
    else:
        raise RuntimeError(
            "batch is not GAX or VCC (type is %s)"
            % reference_file.reference_file_type.reference_file_type_description
        )
