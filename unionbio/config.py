import logging
from flytekit import ImageSpec

# Setup the logger
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("[%(asctime)s %(levelname)s %(name)s] %(message)s")
)
logger.addHandler(console_handler)
logger.setLevel(logging.DEBUG)

current_registry = "localhost:30000"

folding_img = ImageSpec(
    name="unionbio-protein",
    # base_image="ghcr.io/flyteorg/flytekit:py3.11-1.12.0",
    python_version="3.11",
    packages=["flytekit"],
    conda_channels=["bioconda", "conda-forge"],
    conda_packages=[
        "prodigal",
        "biotite", 
        "biopython",
        "py3Dmol"
        ],
    registry=current_registry,
    platform="linux/amd64",
)

parabricks_img = ImageSpec(
    name="unionbio-parabricks",
    base_image="nvcr.io/nvidia/clara/clara-parabricks:4.3.0-1",
    python_version="3.10",
    packages=["flytekit"],
    registry=current_registry,
)

main_img = ImageSpec(
    name="unionbio-main",
    base_image="ghcr.io/flyteorg/flytekit:py3.11-1.12.0",
    python_version="3.11",
    conda_channels=["bioconda"],
    conda_packages=[
        "samtools",
        "bcftools",
        "bwa",
        "fastp",
        "hisat2",
        "bowtie2",
        "gatk4",
        "fastqc",
        "htslib"
        ],
    builder="fast-builder",
    registry=current_registry,
)

seq_dir_pth = "s3://my-s3-bucket/my-data/sequences"
ref_loc = "s3://my-s3-bucket/my-data/refs/GRCh38_short.fasta"
ref_hash = str(hash(ref_loc))[:4]

# Tool config
fastp_cpu = "3"

