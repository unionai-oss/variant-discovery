from unionbio.config import folding_img, parabricks_img, main_img
from flytekit.image_spec.image_spec import ImageBuildEngine

# Build the images
builder = ImageBuildEngine()
builder.build(folding_img.with_packages("pytest"))

# builder.build(parabricks_img)
# builder.build(main_img)