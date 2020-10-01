import massgov.pfml.bofa.generate as generate


def test_ccor_generator():
    builder = generate.CcorGenerator()
    builder.add_buyer_record(errors=[generate.ERR_DATA_NOT_NUMERIC])
    builder.add_buyer_record()
    builder.add_cardholder_record()
    builder.add_cardholder_record(errors=[generate.ERR_MISSING_REQUIRED_FIELD_DB])
    ccor = builder.build_ccor()
    ccor_lines = ccor.split("\n")

    # File Header, Processed Header, Processed Trailer, Non-Processed Header, Non-Processed Trailer, File Trailer, 4 records, 2 non-processed errors
    assert len(ccor_lines) == 12

    file_header_tokens = ccor_lines[0].split(",")
    assert len(file_header_tokens) == 9  # 8 + trailing comma
    assert file_header_tokens[0] == "DPSHEADER "

    processed_header_tokens = ccor_lines[1].split(",")
    assert len(processed_header_tokens) == 2  # 1 + trailing comma
    assert processed_header_tokens[0] == "BH-PROCESSED"

    processed_buyer_tokens = ccor_lines[2].split(",")
    assert len(processed_buyer_tokens) == 63  # 63, spec includes the trailing comma as a field
    assert processed_buyer_tokens[0] == "B"

    processed_cardholder_tokens = ccor_lines[3].split(",")
    assert len(processed_cardholder_tokens) == 47  # 46 + trailing comma
    assert processed_cardholder_tokens[0] == "C"

    processed_trailer_tokens = ccor_lines[4].split(",")
    assert len(processed_trailer_tokens) == 5  # 4 + trailing comma
    assert processed_trailer_tokens[0] == "BT-PROCESSED"

    nonprocessed_header_tokens = ccor_lines[5].split(",")
    assert len(nonprocessed_header_tokens) == 2  # 1 + trailing comma
    assert nonprocessed_header_tokens[0] == "BH-NONPROCESSED"

    nonprocessed_buyer_tokens = ccor_lines[6].split(",")
    assert len(nonprocessed_buyer_tokens) == 63  # 63, spec includes the trailing comma as a field
    assert nonprocessed_buyer_tokens[0] == "B"

    buyer_error_tokens = ccor_lines[7].split(",")
    assert len(buyer_error_tokens) == 12  # 11 + trailing comma
    assert buyer_error_tokens[0] == "E"

    nonprocessed_cardholder_tokens = ccor_lines[8].split(",")
    assert len(nonprocessed_cardholder_tokens) == 43  # 42 + trailing comma
    assert nonprocessed_cardholder_tokens[0] == "C"

    cardholder_error_tokens = ccor_lines[9].split(",")
    assert len(cardholder_error_tokens) == 12  # 11 + trailing comma
    assert cardholder_error_tokens[0] == "E"

    nonprocessed_trailer_tokens = ccor_lines[10].split(",")
    assert len(nonprocessed_trailer_tokens) == 6  # 5 + trailing comma
    assert nonprocessed_trailer_tokens[0] == "BT-NONPROCESSED"

    file_trailer_tokens = ccor_lines[11].split(",")
    assert len(file_trailer_tokens) == 8  # 7 + trailing comma
    assert file_trailer_tokens[0] == "DPSTRAILER"


def test_ccor_generator_overrides():
    # For simplicity, this overrides the 2nd item in each line.
    general_params = {}
    general_params["client_identifier"] = "OverrideValue"

    buyer_params = {}
    buyer_params["card_program_type"] = "9"

    cardholder_params = {}
    cardholder_params["client_tracking_id"] = "0123456789"

    builder = generate.CcorGenerator(general_params)
    builder.add_buyer_record(buyer_params)
    builder.add_cardholder_record(cardholder_params)
    ccor = builder.build_ccor()
    ccor_lines = ccor.split("\n")

    # File Header, Processed Header, Processed Trailer, Non-Processed Header, Non-Processed Trailer, File Trailer, 2 records
    assert len(ccor_lines) == 8

    file_header_tokens = ccor_lines[0].split(",")
    assert file_header_tokens[1] == "OverrideValue"

    buyer_tokens = ccor_lines[2].split(",")
    assert buyer_tokens[1] == "9"

    cardholder_tokens = ccor_lines[3].split(",")
    assert cardholder_tokens[1] == "0123456789"


def test_ccor_generator_multiple_errors():
    builder = generate.CcorGenerator()
    builder.add_buyer_record(
        errors=[
            generate.ERR_DATA_NOT_NUMERIC,
            generate.ERR_MISSING_REQUIRED_FIELD_PREV_FIELD,
            generate.ERR_MISSING_REQUIRED_FIELD_DB,
        ]
    )

    ccor = builder.build_ccor()
    ccor_lines = ccor.split("\n")

    # File Header, Processed Header, Processed Trailer, Non-Processed Header, Non-Processed Trailer, File Trailer, 1 non-processed record with 3 errors
    assert len(ccor_lines) == 10

    err1_tokens = ccor_lines[5].split(",")
    assert err1_tokens[0] == "E"

    err2_tokens = ccor_lines[6].split(",")
    assert err2_tokens[0] == "E"

    err3_tokens = ccor_lines[7].split(",")
    assert err3_tokens[0] == "E"

    # Grab the error descriptions, which are the next to last element (last element is always empty due to trailing comma)
    err_descriptions = [err1_tokens[-2], err2_tokens[-2], err3_tokens[-2]]
    assert generate.ERR_MISSING_REQUIRED_FIELD_DB["description"] in err_descriptions
    assert generate.ERR_MISSING_REQUIRED_FIELD_PREV_FIELD["description"] in err_descriptions
    assert generate.ERR_DATA_NOT_NUMERIC["description"] in err_descriptions

    # Make sure the error counts are correct by checking the trailer
    file_trailer_tokens = ccor_lines[-1].split(",")
    assert int(file_trailer_tokens[3]) == 1  # Buyer count
    assert int(file_trailer_tokens[4]) == 0  # Cardholder count
    assert int(file_trailer_tokens[5]) == 3  # Error count
    assert int(file_trailer_tokens[6]) == 4  # Total count
