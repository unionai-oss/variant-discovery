from mashumaro.mixins.json import DataClassJSONMixin
from dataclasses import dataclass
from flytekit.types.directory import FlyteDirectory
from config import logger
from pathlib import Path


@dataclass
class Reference(DataClassJSONMixin):
    """
    Represents a reference FASTA and associated index files.

    This class captures a directory containing a reference FASTA and optionally it's associated
    index files. 

    Attributes:
        ref_name (str): Name or identifier of the raw sequencing sample.
        ref_dir (FlyteDirectory): Directory containing the reference and any index files.
        index_name (str): Index string to pass to tools requiring it. Some tools require just the 
        ref name and assume index files are in the same dir, others require the index name.
        indexed_with (str): Name of tool used to create the index.
    """

    ref_name: str
    ref_dir: FlyteDirectory
    index_name: str | None = None
    indexed_with: str | None = None