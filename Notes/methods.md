
&nbsp;

# JSON Functions:

| JSON Function           | What it does               | Direction  |
| ----------------------- | -------------------------- | ---------- |
| `json.load(file)`       | File ➜ Python (list/dict)  | ← Read     |
| `json.dump(data, file)` | Python ➜ File (text .json) | → Write    |
| `json.loads(string)`    | String ➜ Python            | ← Parse    |
| `json.dumps(data)`      | Python ➜ JSON string       | → Generate |

&nbsp;

&nbsp;


# OS Functions:

| `os` Function                 | What it does                           | Direction     |
| ----------------------------- | -------------------------------------- | ------------- |
| `os.path.exists(path)`        | Checks if the file/folder exists       | ← Check       |
| `os.path.basename(path)`      | Gets file name from full path          | ← Extract     |
| `os.path.join(a, b)`          | Joins parts into a proper path         | → Build       |
| `os.rename(src, dest)`        | Renames or moves file                  | → Rename/Move |
| `os.walk(directory)`          | Recursively walks all folders/files    | ← Iterate     |
| `os.makedirs(path, exist_ok)` | Creates folders (recursively)          | → Create      |
| `os.remove(path)`             | Deletes a file                         | → Delete      |
| `os.listdir(path)`            | Lists all files/folders in a directory | ← Read        |
| `os.getcwd()`                 | Gets current working directory         | ← Get         |
| `os.chdir(path)`              | Changes current working directory      | → Change      |

&nbsp;

&nbsp;


# ZipFile Functions:

| `zipfile` Function                     | What it does                                         | Direction  |
| -------------------------------------- | ---------------------------------------------------- | ---------- |
| `zipfile.ZipFile(path, mode)`          | Opens a zip file in read/write mode                  | ↔ Access   |
| `zipf.extractall(dest_path)`           | Extracts all files from zip to destination folder    | → Unzip    |
| `zipf.write(file_path, arcname)`       | Adds file to zip archive with optional internal name | → Add      |
| `zipf.namelist()`                      | Lists file names inside the zip                      | ← Inspect  |
| `zipf.close()` *(or use `with` block)* | Closes the zip archive                               | → Close    |
| `zipfile.is_zipfile(path)`             | Checks if a given file is a valid zip archive        | ← Validate |
