import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from mypy_boto3_builder.cli_parser import Namespace
from mypy_boto3_builder.main import get_available_service_names, get_selected_service_names, main
from mypy_boto3_builder.service_name import ServiceName
from mypy_boto3_builder.utils.boto3_changelog import Boto3Changelog


class TestMain:
    def test_get_selected_service_names(self) -> None:
        assert [
            i.name
            for i in get_selected_service_names(
                ["s3", "ec2"], [ServiceName("ec2", "EC2"), ServiceName("other", "Other")]
            )
        ] == ["ec2"]
        assert [
            i.name
            for i in get_selected_service_names(
                ["all", "ec2"], [ServiceName("ec2", "EC2"), ServiceName("other", "Other")]
            )
        ] == ["ec2", "other"]
        assert get_selected_service_names(["s3", "ec2"], []) == []
        with patch.object(Boto3Changelog, "get_updated_service_names", lambda x, y: ["ecs"]):
            assert [
                i.name
                for i in get_selected_service_names(
                    ["updated", "ec2"],
                    [
                        ServiceName("ec2", "EC2"),
                        ServiceName("ecs", "ECS"),
                        ServiceName("other", "Other"),
                    ],
                )
            ] == ["ec2", "ecs"]

    def test_get_available_service_names(self) -> None:
        session_mock = MagicMock()
        session_mock.get_available_services.return_value = ["s3", "ec2", "unsupported"]
        session_mock._session.get_service_data.return_value = {
            "metadata": {"serviceAbbreviation": "Amazon S3", "serviceId": "s3"}
        }
        assert len(get_available_service_names(session_mock)) == 3

    @patch("mypy_boto3_builder.main.Boto3Generator")
    @patch.object(sys, "argv", ["-o", "/tmp", "-b", "1.2.3.post4"])
    def test_main(self, Boto3GeneratorMock: MagicMock) -> None:
        main()
        Boto3GeneratorMock().generate_stubs.assert_called()
        Boto3GeneratorMock().generate_service_stubs.assert_called()
