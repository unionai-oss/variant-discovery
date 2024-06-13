import os
import re
import subprocess as sp
from pathlib import Path
from dataclasses import dataclass
from flytekit import ImageSpec
from flytekit.image_spec.image_spec import ImageBuildEngine

current_registry = "localhost:30000"
test_rt = Path(__file__).parent
prod_rt = test_rt.joinpath("src")

main_img = ImageSpec(
    name="unionbio-main",
    source_root=prod_rt,
    packages=["flytekit"],
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
        "htslib",
    ],
    builder="fast-builder",
    registry=current_registry,
)

folding_img = ImageSpec(
    name="unionbio-protein",
    platform="linux/amd64",
    python_version="3.11",
    source_root=prod_rt,
    packages=["flytekit", "transformers", "torch"],
    conda_channels=["bioconda", "conda-forge"],
    conda_packages=[
        "prodigal",
        "biotite",
        "biopython",
        "py3Dmol",
        "matplotlib",
    ],
    registry=current_registry,
)

parabricks_img = ImageSpec(
    name="unionbio-parabricks",
    base_image="nvcr.io/nvidia/clara/clara-parabricks:4.3.0-1",
    source_root=prod_rt,
    python_version="3.10",
    packages=["flytekit"],
    registry=current_registry,
)


class ImageFactory:
    def __init__(self):
        self.config_path = Path("src/unionbio/config.py")
        self.build_scope = [
            "main_img",
            # "folding_img",
            # "parabricks_img",
        ]
        self.fqns = {}
        self.build_specs = []

    # def built_wheel(self, output_dirname: str = "unionbio", fmt: str = "wheel") -> str:
    #     """Build the wheel package using Poetry and return the wheel file name."""

    #     # Build package
    #     result = sp.run(
    #         ["poetry", "build", "-o", output_dirname, "-f", fmt],
    #         capture_output=True,
    #         text=True,
    #     )

    #     # Check if the command was successful
    #     if result.returncode != 0:
    #         print(f"Poetry build failed with exit code {result.returncode}")
    #         print(result.stderr)
    #         exit(1)

    #     # Extract the wheel name from the output
    #     output = result.stdout
    #     matches = re.findall(r"unionbio.*\.whl", output)
    #     if matches and len(matches) == 1:
    #         wheel = matches[0]
    #     else:
    #         print("Wheel file name not found in the output")
    #         exit(1)

    #     # return f"{output_dirname}/{wheel}"
    #     return wheel

    def update_img_config(self):

        with open(self.config_path, "r") as f:
            cfg_content = f.read()

        for var, tag in self.fqns.items():
            cfg_content = re.sub(rf"{var} = .+", f'{var} = "{tag}"', cfg_content)

        with open(self.config_path, "w") as f:
            f.write(cfg_content)

    def build_all(self):

        self.update_img_config()
        # whl = self.built_wheel()

        # Build images
        for spec in self.build_specs:
            # spec.packages.append(whl)
            ImageBuildEngine().build(spec)


def build():
    factory = ImageFactory()

    # Prepare builds
    for img_str in factory.build_scope:
        spec = eval(img_str)
        factory.fqns[f"{img_str}_fqn"] = spec.image_name()
        factory.build_specs.append(spec)

    factory.build_all()

def build_test():
    factory = ImageFactory()
    factory.config_path = Path("tests/config.py")

    # Prepare builds
    for img_str in factory.build_scope:
        spec = eval(img_str)
        spec.name = f"{spec.name}-test"
        spec.source_root = test_rt
        spec.packages.append("pytest")
        factory.fqns[f"{img_str}_test_fqn"] = spec.image_name()
        factory.build_specs.append(spec)

    factory.build_all()

