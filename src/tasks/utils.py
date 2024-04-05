import os
import zipfile
import requests
import tarfile
import gzip
from pathlib import Path
from typing import List
from flytekit import task, current_context
from flytekit.types.directory import FlyteDirectory
from flytekit.types.file import FlyteFile
from flytekit.configuration import Config
from flytekit.remote import FlyteRemote
from flytekit.extras.tasks.shell import subproc_execute

from config import base_image, logger, pb_image
from datatypes.reads import Reads

def fetch_file(url: str, local_dir: Path) -> Path:
    """
    Downloads a file from the specified URL.

    Args:
        url (str): The URL of the tar.gz file to download.
        local_dir (Path): The directory where you would like this file saved.

    Returns:
        Path: The local path to the decompressed file.

    Raises:
        requests.HTTPError: If an HTTP error occurs while downloading the file.
    """
    try:
        response = requests.get(url)
        fname = url.split("/")[-1]
        local_path = local_dir.joinpath(fname)
        with open(local_path, "wb") as file:
            file.write(response.content)
    except requests.HTTPError as e:
        print(f"HTTP error: {e}")
        raise e
    return local_path

@task(container_image=base_image)
def prepare_raw_samples(seq_dir: FlyteDirectory) -> List[Reads]:
    """
    Prepare and process raw sequencing data to create a list of RawSample objects.

    This function processes raw sequencing data located in the specified input directory
    and prepares it to create a list of RawSample objects.

    Args:
        seq_dir (FlyteDirectory): The input directory containing raw sequencing data.

    Returns:
        List[RawSample]: A list of RawSample objects representing the processed sequencing data.
    """
    seq_dir.download()
    return Reads.make_all(Path(seq_dir))

@task(cache=True, cache_version=1)
def fetch_files(urls: List[str], decompress: bool) -> List[FlyteFile]:
    """
    Downloads a file from the specified URL, decompresses it, and returns a FlyteFile object.

    Args:
        urls (List[str]): A list of URLs to the files to download.

    Returns:
        Path: The local path to the decompressed file.

    Raises:
        requests.HTTPError: If an HTTP error occurs while downloading the file.
    """
    outfiles = []
    for url in urls:
        lpath = fetch_file(url, current_context().working_directory)
        if decompress and 'gz' in lpath:
            dlpath = lpath.with_suffix('')
            with gzip.open(lpath, 'rb') as f_in:
                with open(dlpath, 'wb') as f_out:
                    f_out.write(f_in.read())
            outfiles.append(FlyteFile(path=dlpath))
        else:
            outfiles.append(FlyteFile(path=lpath))
    
@task
def fetch_tarfile(url: str) -> FlyteDirectory:
    """
    Downloads a tar.gz file from the specified URL, extracts its contents, and returns a FlyteDirectory object.

    Args:
        url (str): The URL of the tar.gz file to download.

    Returns:
        FlyteDirectory: A FlyteDirectory object representing the directory where the contents of the tar.gz file were extracted.

    Raises:
        requests.HTTPError: If an HTTP error occurs while downloading the file.
    """
    try:
        response = requests.get(url)
        tar_name = url.split("/")[-1]
        with open(tar_name, "wb") as file:
            file.write(response.content)
    except requests.HTTPError as e:
        print(f"HTTP error: {e}")
        raise e

    working_dir = current_context().working_directory
    out_dir = Path(os.path.join(working_dir, tar_name))
    with tarfile.open(tar_name, "r:gz") as tarf:
        tarf.extractall(out_dir)

    return FlyteDirectory(path=out_dir)


@task
def check_fastqc_reports(rep_dir: FlyteDirectory) -> str:
    """
    Check FastQC reports for errors.

    This function checks FastQC reports for errors and raises an exception if any are found.

    Args:
        rep_dir (FlyteDirectory): The input directory containing FastQC reports.
    """
    rep_dir.download()
    all_zips = list(Path(rep_dir.path).rglob("*fastqc.zip*"))

    for p in all_zips:
        logger.debug(f"Checking {p}")
        with zipfile.ZipFile(p, "r") as zip_file:
            logger.debug(f"{zip_file.filename}")
            logger.debug(f"Archive contains {zip_file.namelist()}")
            with zip_file.open(
                f"{Path(zip_file.filename).stem}/summary.txt"
            ) as summary:
                contents = summary.read().decode("utf-8")
                logger.debug(f"Contents of summary.txt: {contents}")
                if "FAIL" in contents:
                    return "FAIL"
                elif "WARN" in contents:
                    return "WARN"

    return "PASS"


def get_remote(local=None, config_file=None):
    """
    Get remote configuration settings and return a remote object.

    This function retrieves remote configuration settings, including the local flag and
    a configuration file, and uses them to create and return a remote object.

    Args:
        local (bool, optional): A flag indicating whether to use local settings. If True,
            the function will use local settings; if False, it will use remote settings.
            Defaults to None, which implies the use of default settings.
        config_file (str, optional): The path to a custom configuration file. If provided,
            this file will be used for configuration settings. Defaults to None.

    Returns:
        Remote: A remote object configured with the specified settings.
    """
    return FlyteRemote(
        config=Config.auto(
            config_file=(
                None
                if local
                else config_file
                if config_file is not None
                else str(Path.home() / ".flyte" / "config-sandbox.yaml")
            )
        ),
        default_project="flytesnacks",
        default_domain="development",
    )


@task(container_image=pb_image)
def compare_bams(in1: FlyteFile, in2: FlyteFile) -> bool:
    """
    Compares two BAM files and returns True if they are identical, False otherwise.

    Args:
        in1 (FlyteFile): The first input BAM file.
        in2 (FlyteFile): The second input BAM file.

    Returns:
        bool: True if the BAM files are identical, False otherwise.
    """
    in1.download()
    in2.download()

    cmp1 = [
        "bam",
        "diff",
        "--in1",
        in1.path,
        "--in2",
        in2.path,
        "--noCigar",
        "--isize",
        "--flag",
        "--mate",
        "--mapQual",
    ]

    out, err = subproc_execute(cmp1)

    no_out = out == "" and err == ""

    return no_out
