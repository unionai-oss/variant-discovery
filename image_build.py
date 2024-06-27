from flytekit import ImageSpec
from flytekit.image_spec.image_spec import ImageBuildEngine
from imagespec_fast_builder import FastImageBuilder

base_image = ImageSpec(
    name="variant-discovery",
    python_version="3.10",
    builder="fast-builder",
    requirements="requirements.txt",
    source_root="src",
    apt_packages=["fontconfig", "fonts-dejavu"],
    conda_packages=[
        "fastqc==0.12.1",
        "fastp==0.23.4",
        "bwa",
        "samtools==1.17",
        "gatk4==4.4.0.0",
    ],
    conda_channels=["bioconda"],
    registry="localhost:30000",
)

FastImageBuilder()._build_image(base_image, push=False)
