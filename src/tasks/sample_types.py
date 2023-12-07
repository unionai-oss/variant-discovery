from mashumaro.mixins.json import DataClassJSONMixin
from dataclasses import dataclass
from flytekit.types.file import FlyteFile
from flytekit.types.directory import FlyteDirectory
from flytekit import task
from config import base_image
from pathlib import Path
from typing import List


@dataclass
class RawSample(DataClassJSONMixin):
    """
    Represents a raw sequencing sample via its associated files.

    This class defines the structure for representing a raw sequencing sample. It includes
    attributes for the sample name and paths to the raw read files (R1 and R2).

    Attributes:
        sample (str): The name or identifier of the raw sequencing sample.
        raw_r1 (FlyteFile): A FlyteFile object representing the path to the raw R1 read file.
        raw_r2 (FlyteFile): A FlyteFile object representing the path to the raw R2 read file.
    """

    sample: str = ""
    raw_r1: FlyteFile = FlyteFile(path="/dev/null")
    raw_r2: FlyteFile = FlyteFile(path="/dev/null")



@dataclass
class FiltSample(DataClassJSONMixin):
    """
    Represents a filtered sequencing sample with its associated files and a quality report.

    This class defines the structure for representing a filtered sequencing sample. It includes
    attributes for the sample name, paths to the filtered read files (R1 and R2), and a quality
    report.

    Attributes:
        sample (str): The name or identifier of the filtered sequencing sample.
        filt_r1 (FlyteFile): A FlyteFile object representing the path to the filtered R1 read file.
        filt_r2 (FlyteFile): A FlyteFile object representing the path to the filtered R2 read file.
        report (FlyteFile): A FlyteFile object representing the quality report associated with
            the filtered sample.
    """

    sample: str
    filt_r1: FlyteFile = FlyteFile(path="/dev/null") 
    filt_r2: FlyteFile = FlyteFile(path="/dev/null")
    report: FlyteFile = FlyteFile(path="/dev/null")


@dataclass
class SamFile(DataClassJSONMixin):
    """
    Represents a SAM (Sequence Alignment/Map) file and its associated sample and report.

    This class defines the structure for representing a SAM file along with attributes
    that describe the associated sample and report.

    Attributes:
        sample (str): The name or identifier of the sample to which the SAM file belongs.
        sam (FlyteFile): A FlyteFile object representing the path to the SAM file.
        report (FlyteFile): A FlyteFile object representing an associated report
            for performance of the aligner.
    """

    sample: str
    sam: FlyteFile = FlyteFile(path="/dev/null")
    report: FlyteFile = FlyteFile(path="/dev/null")

registry = [
    List[RawSample],
    List[FiltSample],
    List[SamFile],
]

@task(container_image=base_image)
def prepare_raw_samples(seq_dir: FlyteDirectory) -> List[RawSample]: # eventually replace with Union[*registry]
    """
    Prepare and process raw sequencing data to create a list of RawSample objects.

    This function processes raw sequencing data located in the specified input directory
    and prepares it to create a list of RawSample objects.

    Args:
        seq_dir (FlyteDirectory): The input directory containing raw sequencing data.

    Returns:
        List[RawSample]: A list of RawSample objects representing the processed sequencing data.
    """
    samples = {}

    # Fetch FlyteDirectory from object storage and make
    # list of relevant paths
    seq_dir.download()
    all_paths = list(Path(seq_dir.path).rglob("*fastq.gz*"))

    for fp in all_paths:
        # Parse paths following 'sample_read.fastq.gz' format
        fn = fp.name
        fullname = fn.split(".")[0]
        sample, mate = fullname.split("_")[0:2]

        if not samples.get(sample):
            samples[sample] = RawSample(
                sample=sample,
            )

        print(f"Working on {fn} with mate {mate} for sample {sample}")
        if mate == "1":
            setattr(samples[sample], "raw_r1", FlyteFile(path=str(fp)))
        elif mate == "2":
            setattr(samples[sample], "raw_r2", FlyteFile(path=str(fp)))

    return list(samples.values())