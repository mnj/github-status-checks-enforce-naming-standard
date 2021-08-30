# github-status-checks-enforce-naming-standard
Makes sure the files updated with a pull requests follow the naming standard (in this case lowercase files/folders)

Probably not super usefull for anyone else.

There is a few options you can specify:
| Input                        | Description                                          | Required? | Default       |
|------------------------------|------------------------------------------------------|-----------|---------------|
| require_lowercase_filenames  | Whether all file names should be lowercase           | Yes       | true          |
| require_lowercase_foldername | Whether all folder names should be lowercase         | Yes       | true          |
| excluded_files               | JSON list of filenames to exclude                    | No        | ["README.md"] |
| excluded_folders             | JSON list of folders to  exclude                     | No        | []            |
| github_token                 | The GITHUB_TOKEN to use for authenticating to github | No        | N/A           |

Please note, excluded_folders, should be the full path of the folder, as seen from the root of the repo, e.g Folder1/Subfolder without a trailing slash.

## Example status check Github Action workflow simple
```yml
name: Enforce naming standard

on: [pull_request]

jobs:
  enforce-naming-standard:
    runs-on: ubuntu-latest
    steps:
      - uses: mnj/github-status-checks-enforce-naming-standard@v1
        with:
          require_lowercase_filenames: 'true'
          require_lowercase_folders: 'true'
          excluded_files: '["README.md"]'
          excluded_folders: '[]'
          github_token: ${{ secrets.GITHUB_TOKEN }}
```
