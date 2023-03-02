run:
	poetry run python -B main.py

# If the first argument is "convert"
ifeq (convert,$(firstword $(MAKECMDGOALS)))
  RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(RUN_ARGS):;@:)
endif
# convert <gltf_file> <bam_file>
convert:
	gltf2bam $(RUN_ARGS)