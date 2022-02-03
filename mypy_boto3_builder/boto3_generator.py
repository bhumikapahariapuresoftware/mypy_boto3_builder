"""
Boto3 stubs/docs generator.
"""
from collections.abc import Iterable, Sequence
from pathlib import Path

from boto3 import __version__ as boto3_version
from boto3.session import Session
from botocore import __version__ as botocore_version

from mypy_boto3_builder.constants import BOTO3_STUBS_NAME, BOTOCORE_STUBS_NAME, PYPI_NAME
from mypy_boto3_builder.jinja_manager import JinjaManager
from mypy_boto3_builder.logger import get_logger
from mypy_boto3_builder.service_name import ServiceName
from mypy_boto3_builder.utils.pypi_manager import PyPIManager
from mypy_boto3_builder.writers.processors import (
    process_boto3_stubs,
    process_boto3_stubs_docs,
    process_botocore_stubs,
    process_master,
    process_service,
    process_service_docs,
)


class Boto3Generator:
    """
    Boto3 stubs/docs generator.

    Arguments:
        service_names -- Enabled service names
        available_service_names -- All service names
        master_service_names -- Service names included in master
        session -- Botocore session
        output_path -- Path to write generated files
        generate_setup -- Whether to create package or installed module
        skip_published -- Whether to skip packages that are already published
        bump_on_published -- Whether to create a new postrelease if version is already published
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
        bump_on_published: bool,
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
        self.bump_on_published = bump_on_published
        self.version = version

    def _get_package_version(self, pypi_name: str, version: str) -> str | None:
        pypi_manager = PyPIManager(pypi_name)
        if not pypi_manager.has_version(version):
            return version

        if self.skip_published:
            return None
        if not self.bump_on_published:
            return version

        return pypi_manager.get_next_version(version)

    def _generate_master(self) -> None:
        """
        Generate `mypy-boto3` package.
        """
        version = self._get_package_version(PYPI_NAME, self.version)
        if not version:
            self.logger.info(f"Skipping {PYPI_NAME} {self.version}, already on PyPI")
            return

        self.logger.info(f"Generating {PYPI_NAME} {version}")
        process_master(
            self.session,
            self.output_path,
            service_names=self.service_names,
            generate_setup=self.generate_setup,
            version=version,
        )

    def _generate_boto3_stubs(self) -> None:
        """
        Generate `boto3-stubs` package.
        """
        version = self._get_package_version(PYPI_NAME, self.version)
        if not version:
            self.logger.info(f"Skipping {BOTO3_STUBS_NAME} {self.version}, already on PyPI")
            return

        self.logger.info(f"Generating {BOTO3_STUBS_NAME} {version}")
        process_boto3_stubs(
            self.session,
            self.output_path,
            self.service_names,
            generate_setup=self.generate_setup,
            version=version,
        )

    def _generate_botocore_stubs(self) -> None:
        """
        Generate `botocore-stubs` package.
        """
        version = self._get_package_version(BOTOCORE_STUBS_NAME, botocore_version)
        if not version:
            self.logger.info(f"Skipping {BOTOCORE_STUBS_NAME} {botocore_version}, already on PyPI")
            return

        JinjaManager.update_globals(
            botocore_build_version=version,
        )

        self.logger.info(f"Generating {BOTOCORE_STUBS_NAME} {version}")
        process_botocore_stubs(
            self.output_path,
            generate_setup=self.generate_setup,
        )

    def generate_stubs(self) -> None:
        """
        Generate main stubs.
        """
        if not self.generate_setup:
            self._generate_master()

        self._generate_boto3_stubs()
        self._generate_botocore_stubs()

    def generate_service_stubs(self) -> None:
        """
        Generate service stubs.
        """
        total_str = f"{len(self.service_names)}"
        for index, service_name in enumerate(self.service_names):
            current_str = f"{{:0{len(total_str)}}}".format(index + 1)
            service_name.boto3_version = boto3_version

            version = self._get_package_version(service_name.pypi_name, self.version)
            if not version:
                self.logger.info(
                    f"[{current_str}/{total_str}]"
                    f" Skipping {service_name.module_name} {self.version}, already on PyPI"
                )
                continue

            self.logger.info(
                f"[{current_str}/{total_str}]" f" Generating {service_name.module_name} {version}"
            )
            process_service(
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
        for index, service_name in enumerate(self.service_names):
            current_str = f"{{:0{len(total_str)}}}".format(index + 1)
            logger.info(
                f"[{current_str}/{total_str}] Generating {service_name.module_name} module docs"
            )
            process_service_docs(
                session=self.session,
                output_path=self.output_path,
                service_name=service_name,
                service_names=self.available_service_names,
            )

        logger.info(f"Generating {BOTO3_STUBS_NAME} module docs")
        process_boto3_stubs_docs(
            self.session,
            self.output_path,
            self.service_names,
        )