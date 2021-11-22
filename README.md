# GIT ChangeLog Creator

## Usage
1. Install requirements dependencies:
```bash
pip3 install -r requirements.txt
```
2. Set permissions to `changelog.py`:
```bash
chmod +x changelog.py
```
3. To process repository and create changelog:  
```bash
./changelog.py [-h] [--path-repo PATH] [--outfile OUTFILE] [--since SINCE] [--auto-name] [--repo-name NAME] [--date-group] [--format FORMAT] [--log-level LEVEL]
```

## optional arguments:
```bash
  -h, --help         show this help message and exit
  --path-repo PATH   GIT Repository path. Default: ./
  --outfile OUTFILE  Output file path. Default: No output
  --since SINCE      GIT log since date. Format YYYY-MM-DD. Default: From begin of time
  --auto-name        Try to autodiscover Repository name. Default: True
  --repo-name NAME   Repository Name
  --date-group       Get the commit dates and group by them. Default: False
  --format FORMAT    Output format. Default: md (MarkDown). Valid formats: md, json
  --log-level LEVEL  Log level. Default: WARNING
```
