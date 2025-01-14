"""
AIOBotocore stubs/docs generator.
"""
from collections.abc import Iterable, Sequence
from pathlib import Path

from boto3 import __version__ as boto3_version
from boto3.session import Session

from mypy_boto3_builder.constants import AIOBOTOCORE_PYPI_NAME, AIOBOTOCORE_STUBS_LITE_PYPI_NAME
from mypy_boto3_builder.logger import get_logger
from mypy_boto3_builder.service_name import ServiceName
from mypy_boto3_builder.utils.pypi_manager import PyPIManager
from mypy_boto3_builder.writers.aiobotocore_processors import (
    process_aiobotocore_service,
    process_aiobotocore_service_docs,
    process_aiobotocore_stubs,
    process_aiobotocore_stubs_docs,
    process_aiobotocore_stubs_lite,
)


class AioBotocoreGenerator:
    """
    AioBotocore stubs/docs generator.

    Arguments:
        service_names -- Enabled service names
        available_service_names -- All service names
        master_service_names -- Service names included in master
        session -- Botocore session
        output_path -- Path to write generated files
        generate_setup -- Whether to create package or installed module
        skip_published -- Whether to skip packages that are already published
        disable_smart_version -- Whether to create a new postrelease if version is already published
        version -- Package build version
    """

    def __init__(
        self,
        service_names: Sequence[ServiceName],
        available_service_names: Iterable[ServiceName],
        master_service_names: Sequence[ServiceName],
        session: Session,
        output_path: Path,
        generate_setup: bool,
        skip_published: bool,
        disable_smart_version: bool,
        version: str,
    ):
        self.session = session
        self.service_names = service_names
        self.available_service_names = available_service_names
        self.master_service_names = master_service_names
        self.output_path = output_path
        self.logger = get_logger()
        self.generate_setup = generate_setup
        self.skip_published = skip_published
        self.disable_smart_version = disable_smart_version
        self.version = version

    def _get_package_version(self, pypi_name: str, version: str) -> str | None:
        pypi_manager = PyPIManager(pypi_name)
        if not pypi_manager.has_version(version):
            return version

        if self.skip_published:
            return None
        if self.disable_smart_version:
            return version

        return pypi_manager.get_next_version(version)

    def generate_stubs(self) -> None:
        """
        Generate `aiobotocore-stubs` package.
        """
        self._generate_stubs()
        self._generate_stubs_lite()

    def _generate_stubs(self) -> None:
        version = self._get_package_version(AIOBOTOCORE_PYPI_NAME, self.version)
        if not version:
            self.logger.info(f"Skipping {AIOBOTOCORE_PYPI_NAME} {self.version}, already on PyPI")
            return

        self.logger.info(f"Generating {AIOBOTOCORE_PYPI_NAME} {version}")
        process_aiobotocore_stubs(
            self.session,
            self.output_path,
            self.service_names,
            generate_setup=self.generate_setup,
            version=version,
        )

    def _generate_stubs_lite(self) -> None:
        version = self._get_package_version(AIOBOTOCORE_STUBS_LITE_PYPI_NAME, self.version)
        if not version:
            self.logger.info(
                f"Skipping {AIOBOTOCORE_STUBS_LITE_PYPI_NAME} {self.version}, already on PyPI"
            )
            return

        self.logger.info(f"Generating {AIOBOTOCORE_STUBS_LITE_PYPI_NAME} {version}")
        process_aiobotocore_stubs_lite(
            self.session,
            self.output_path,
            self.service_names,
            generate_setup=self.generate_setup,
            version=version,
        )

    def generate_service_stubs(self) -> None:
        """
        Generate service stubs.
        """
        total_str = f"{len(self.service_names)}"
        for index, service_name in enumerate(self.service_names):
            current_str = f"{{:0{len(total_str)}}}".format(index + 1)
            service_name.boto3_version = boto3_version

            version = self._get_package_version(service_name.aiobotocore_pypi_name, self.version)
            if not version:
                self.logger.info(
                    f"[{current_str}/{total_str}]"
                    f" Skipping {service_name.aiobotocore_module_name} {self.version}, already on PyPI"
                )
                continue

            self.logger.info(
                f"[{current_str}/{total_str}]"
                f" Generating {service_name.aiobotocore_module_name} {version}"
            )
            process_aiobotocore_service(
                session=self.session,
                output_path=self.output_path,
                service_name=service_name,
                generate_setup=self.generate_setup,
                service_names=self.master_service_names,
                version=version,
            )
            service_name.boto3_version = ServiceName.LATEST

    def generate_docs(self) -> None:
        """
        Generate service and master docs.
        """
        logger = get_logger()
        total_str = f"{len(self.service_names)}"

        logger.info(f"Generating {AIOBOTOCORE_PYPI_NAME} module docs")
        process_aiobotocore_stubs_docs(
            self.session,
            self.output_path,
            self.service_names,
        )

        for index, service_name in enumerate(self.service_names):
            current_str = f"{{:0{len(total_str)}}}".format(index + 1)
            logger.info(
                f"[{current_str}/{total_str}] Generating {service_name.aiobotocore_module_name} module docs"
            )
            process_aiobotocore_service_docs(
                session=self.session,
                output_path=self.output_path,
                service_name=service_name,
                service_names=self.available_service_names,
            )
