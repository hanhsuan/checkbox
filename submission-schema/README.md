# Checkbox submission schema

In this folder you can find the schema for the submission.json that's sent to certification.canonical.com as part of the submission, as well as the instruction and tools needed to recreate that schema.

## The schema

`schema.json` contains the schema that was generated using ~2000 latest (at the time of writing) submissions uploaded to C3.

This json file is referenced by the `docs/reference/submission-schema.rst` file, which is used to generate the 
[submission schema reference documentation](https://checkbox.readthedocs.io/en/latest/reference/submission-schema.html).
Changes in the schema are reflected after successful documentation build.

## Generating schema from scratch

The `schema.json` can be generated using a existing submission tarballs.
Follow the steps below to generate a fresh `schema.json`

> The schema generator is really a utility that helps (helped) create a _starting point_ for the submission JSON schema, and is not for continued use more so than diagnostic purposes (using it serves the purpose of comparing actual submission data against the schema in use, but it is not for example intended to be used regularly to update the canonical schema.json in this directory).

### Obtaining submission tarballs

If you have access to the Hexr repository, you will find a useful
[helper program](https://github.com/canonical/hexr/blob/main/scripts/download_submissions.py) that downloads a series of submissions from C3.

Follow the [README for that tool](https://github.com/canonical/hexr/blob/main/scripts/README.md) to get started.

You will have to tweak the `LIMIT` parameter to download more sessions.
Also note that at the time of writing, this tool is designed to process the submissions
after downloading and then dispose them. Deleting the `os.remove` calls will
make the submission tarballs stay on the filesystem.

### Unpacking submission.json from the tarballs

Navigate to the directory where the downloaded scripts are located, and extract the json files. For instance

```bash
#!/bin/bash

TARGET_DIR="../jsons"

# Create the directory if it doesn't exist.
mkdir -p "$TARGET_DIR"

# Loop through each .tar.xz file in the current directory.
for file in *.tar.xz
do
  # Get the base name of the file without the extension.
  base_name="$(basename "$file" .tar.xz)"

  # Extract only the submission.json file.
  tar -xvf "$file" --wildcards --no-anchored 'submission.json' -O > "${TARGET_DIR}/${base_name}.json"
done

```

### Generating Python loader out of the schema

`quicktype` can be used to generate the schema, as well as Python classes representing submission data.

#### Getting quicktype

1. Install `nodejs` [using the nodesource.com provided Node.js binary distribution](https://github.com/nodesource/distributions#nodejs).

2. Install dependencies (`quicktype` and its transitive dependencies are installed under `./submission-schema/node_modules`).

```bash
cd submission-schema
npm install
```

#### Generating schema with Quicktype from input JSON data

```bash
npm run generate-schema-from-input-jsons
```

#### Generating Python class with Quicktype using the existing schema

```bash
npm run generate-python-types-from-schema
```


#### Generating Python class with Quicktype using submissions

Python classes can be created directly from input JSONs.

```bash
npm run generate-python-types-from-input-jsons
```

#### Simplifying the schema with `manipulate-schema.py`

`manipulate-schema.py` is a tool that helps you manipulate the schema, by removing and renaming definitions included in it.

To replace a type definition with a replacement value, do:

```bash
./collapse-type.py path_to_schema.json definition_to_remove replacement_value -o output_file.json
```

To rename a type definition:

```bash
./collapse-type.py path_to_schema.json old_definition_name -r -n new_definition_name -o output_file.json
```