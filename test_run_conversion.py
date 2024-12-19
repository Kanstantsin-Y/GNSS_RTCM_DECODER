"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com

    Conversion examples and tests.
"""

from run_conversion import main as convert  # pylint: disable = unused-import
from tests.base_data_test_samples import test_base_message
from tests.ephemeris_test_samples import test_eph_message
from tests.msm_test_samples import test_msm_message

# ARGS = r"-o JSON temp\reference-3msg.rtcm3"
# ARGS = r"-o JSON temp\H7V3-A1.rtcm3"
ARGS = r"-o MARGO -i addons.ini temp\RTK134_202102051543.rtcm3"
# ARGS = r"-o MARGO -i addons.ini temp\H7V3-A1.rtcm3"

# ARGS = r"-o JSON RTCM3_TEST_DATA\EPH\msg1045.rtcm3"
# ARGS = r"-o JSON-B RTCM3_TEST_DATA\EPH\msg1019.rtcm3"
# ARGS = r"-o JSON RTCM3_TEST_DATA\EPH\msg1020.rtcm3"
# ARGS = r"-o JSON RTCM3_TEST_DATA\EPH\msg1041.rtcm3"
# ARGS = r"-o JSON RTCM3_TEST_DATA\EPH\msg1042.rtcm3"
# ARGS = r"-o JSON RTCM3_TEST_DATA\EPH\msg1046.rtcm3"

# ARGS = r"-i addons.ini temp\reference-3msg.rtcm3"
# ARGS = None


def test_eph_messages() -> bool:
    """Run test conversion over ephemeris messages"""

    print("Start ephemeris test procedure.")

    summary: list[bool] = []
    summary.append(test_eph_message(1019, "JSON"))
    summary.append(test_eph_message(1020, "JSON"))
    summary.append(test_eph_message(1041, "JSON"))
    summary.append(test_eph_message(1042, "JSON"))
    summary.append(test_eph_message(1045, "JSON"))
    summary.append(test_eph_message(1046, "JSON"))
    summary.append(test_eph_message(1019, "JSON-B"))
    summary.append(test_eph_message(1020, "JSON-B"))
    summary.append(test_eph_message(1041, "JSON-B"))
    summary.append(test_eph_message(1042, "JSON-B"))
    summary.append(test_eph_message(1045, "JSON-B"))
    summary.append(test_eph_message(1046, "JSON-B"))

    print("-" * 80)
    result = "FAILED" if False in summary else "SUCCEED"
    print(f"End ephemeris test procedure. Final result: {result}")

    return result == "SUCCEED"


def test_base_messages() -> bool:
    """Run test conversion over base station messages"""

    print("Start base data test procedure.")

    summary = []

    summary.append(test_base_message(1005, "JSON"))
    summary.append(test_base_message(1006, "JSON"))
    summary.append(test_base_message(1007, "JSON"))
    summary.append(test_base_message(1029, "JSON"))
    summary.append(test_base_message(1033, "JSON"))
    summary.append(test_base_message(1230, "JSON"))
    summary.append(test_base_message(1005, "JSON-B"))
    summary.append(test_base_message(1006, "JSON-B"))
    summary.append(test_base_message(1007, "JSON-B"))
    summary.append(test_base_message(1029, "JSON-B"))
    summary.append(test_base_message(1033, "JSON-B"))
    summary.append(test_base_message(1230, "JSON-B"))

    print("-" * 80)
    result = "FAILED" if False in summary else "SUCCEED"
    print(f"End base data test procedure. Final result: {result}")

    return result == "SUCCEED"


def test_msm_messages() -> bool:
    """Run conversion over MSM messages"""

    print("Start MSM-to-MARGO test procedure.")

    summary = []

    summary.append(test_msm_message(1077, "MARGO"))
    summary.append(test_msm_message(1087, "MARGO"))
    summary.append(test_msm_message(1097, "MARGO"))
    summary.append(test_msm_message(1127, "MARGO"))
    summary.append(test_msm_message(1137, "MARGO"))

    print("-" * 80)
    result = "FAILED" if False in summary else "SUCCEED"
    print(f"End MSM conversion test procedure. Final result: {result}")

    return result == "SUCCEED"


def full_test():
    """Run summary of tests"""

    print("Start full test procedure.")

    summary = []
    summary.append(test_eph_messages())
    summary.append(test_base_messages())
    summary.append(test_msm_messages())

    print("-" * 80)
    summary = "FAILED" if False in summary else "SUCCEED"
    print(f"End full test procedure. Final result: {summary}")


if __name__ == "__main__":

    full_test()

    # test_base_message(1029, 'JSON-B')
    # convert(ARGS)
    # test_base_messages()
    # test_eph_messages()
