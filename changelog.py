#!/usr/bin/env python3

import argparse
import datetime
import json
import logging
import os
from pathlib import Path
import re
import sys
import time

__app_name = "GIT ChangeLog Creator"
__app_version = "1.0.2"


class Format:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


SKIP_WORDS = ['utd', 'wip', 'wtf', 'formater', 'set version', 'App version', 'new version', 'init', 'ver:']
VERSION_WORDS = ['merge branch', 'merge tag', 'pull', 'merge']
VALID_FORMATS = ['md', 'json']


def get_parsed_args():
    arg_parser = argparse.ArgumentParser(description=f'{__app_name} v{__app_version}')
    arg_parser.add_argument(
        '--path-repo', dest='path', action='store',
        type=str, default="./", help='GIT Repository path. Default: ./'
    )
    arg_parser.add_argument(
        '--outfile', dest='outfile', action='store',
        type=str, default="", help='Output file path. Default: No output'
    )
    arg_parser.add_argument(
        '--since', dest='since', action='store',
        type=str, default="", help='GIT log since date. Format YYYY-MM-DD. Default: From begin of time'
    )
    arg_parser.add_argument(
        '--auto-name', dest='auto_repo_name', action='store_true',
        default=True, help='Try to autodiscover Repository name. Default: True'
    )
    arg_parser.add_argument(
        '--repo-name', dest='name', action='store',
        type=str, default="", help='Repository Name'
    )
    arg_parser.add_argument(
        '--date-group', dest='date_group', action='store_true',
        default=False, help='Get the commit dates and group by them. Default: False'
    )
    arg_parser.add_argument(
        '--format', dest='format', action='store',
        type=str, default="md", help=f'Output format. Default: md (MarkDown). Valid formats: {", ".join(VALID_FORMATS)}'
    )
    arg_parser.add_argument(
        '--log-level', dest='level', action='store',
        default='warning', help='Log level. Default: WARNING'
    )
    return arg_parser.parse_args()


def set_logger(level):
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % level)

    handlers = [logging.FileHandler('/tmp/changelog.log'), logging.StreamHandler()]
    logging.basicConfig(
        # encoding='utf-8',
        level=numeric_level,
        format='%(asctime)s [%(levelname)s]: %(message)s',
        # datefmt='%d-%b-%y %H:%M:%S',
        # filename='/tmp/adamo_olt_synchro.log',
        # filemode='a',
        handlers=handlers
    )
    # logging.debug("Debug message...")
    # logging.info("Info message...")
    # logging.warning("Warning message...")
    # logging.error("Error message...")
    # logging.critical("Critical message...")
    # exit(0)


def get_repo_name():
    try:
        f = open('package.json', 'r')
        data = json.load(f)
        name = data['name'].replace("@phicus/", "")
    except Exception:
        name = os.getcwd().split(os.sep)[-1]
    return name


def log_exception(msg, code=1):
    logging.critical(f"{Format.FAIL}{__app_name}: {msg}{Format.ENDC}")
    sys.exit(1)


def get_since(since):
    if since:
        print('Since {}'.format(since if since else 'begin of times'))
        try:
            return datetime.datetime.strptime(since, '%Y-%m-%d')
        except Exception:
            log_exception("Invalid specified since date. Valid format: YYYY-MM-DD")
    return ""


def get_repo(path, since):
    try:
        from pydriller import Repository
        from pydriller import Git
    except Exception:
        log_exception("You must install 'pydriller' library typing: pip3 install pydriller")
    try:
        ggr = Git(path)
        return Repository(path_to_repo=path, since=since) if since else Repository(path_to_repo=path)
    except Exception:
        log_exception(f"Invalid repository path. Specified folder ({path}) doesn't contain a GIT repository")


def parse_message(msg):
    regexp = re.compile(".*(#[\d]+).*")
    rematch = regexp.match(msg)
    issue = rematch.group(1) if rematch else ""
    if issue:
        msg = msg.replace(issue, "").replace(" :", ":") + " (Related to issue: {})".format(issue)
    return msg \
        .replace('add ', 'Add: ') \
        .replace('add:', 'Add:') \
        .replace('Add ', 'Add: ') \
        .replace('fea ', 'Feature: ') \
        .replace('fea:', 'Feature:') \
        .replace('Fea ', 'Feature: ') \
        .replace('Fea:', 'Feature:') \
        .replace('fea?', 'Feature: ') \
        .replace('feature ', 'Feature: ') \
        .replace('fix ', 'Fix: ') \
        .replace('fix:', 'Fix:') \
        .replace('Fix ', 'Fix: ') \
        .replace('ref ', 'Refactor: ') \
        .replace(' ref ', 'Refactor: ') \
        .replace('Ref:', 'Refactor:') \
        .replace('refactor ', 'Refactor: ') \
        .replace('Refactor ', 'Refactor: ') \
        .replace('rfc ', 'Refactor: ') \
        .replace('rfc:', 'Refactor:') \
        .replace('rft ', 'Refactor: ') \
        .replace('rft:', 'Refactor:') \
        .replace('Rft:', 'Refactor:') \
        .replace('enh ', 'Enhancement: ') \
        .replace('Enh ', 'Enhancement: ') \
        .replace('enh:', 'Enhancement:') \
        .replace('Enh:', 'Enhancement:') \
        .replace('enhancement ', 'Enhancement:') \
        .replace('Enhancement ', 'Enhancement:')


def parse_commits(repo):
    try:
        import progressbar
    except Exception:
        log_exception("You must install 'progressbar' library typing: pip3 install progressbar2")

    version = "0.0.0"
    versions = {version: {}}
    commits = list(repo.traverse_commits())
    for commit in progressbar.progressbar(commits):
        if not re.compile('|'.join(SKIP_WORDS), re.IGNORECASE).search(commit.msg) and commit.in_main_branch:
            date = commit.author_date.strftime("%Y-%m-%d")
            if 'release' in commit.msg:
                rematch = re.match(".*[\/]{1}v?([\d.]+).*", commit.msg)
                if rematch:
                    version = rematch.group(1)
                    versions[version] = {}
            if date not in versions[version]:
                versions[version][date] = list()
            if not re.compile('|'.join(VERSION_WORDS), re.IGNORECASE).search(commit.msg):
                if '\n' in commit.msg:
                    for msg in commit.msg.split('\n'):
                        if msg not in versions[version][date]:
                            versions[version][date].append(parse_message(msg))
                else:
                    msg = parse_message(commit.msg)
                    if msg not in versions[version][date]:
                        versions[version][date].append(msg)
    return versions


def get_version(elem):
    version = elem.split('.')
    major = version[0] if len(version) > 0 else '0'
    minor = version[1] if len(version) > 1 else '0'
    patch = version[2] if len(version) > 2 else '0'
    return '{}.{}.{}'.format(major.zfill(4), minor.zfill(4), patch.zfill(4))


def print_md_commits(name, versions, date_group):
    print("# {}".format(name))
    last_date = ""
    for v in sorted(versions, reverse=True, key=get_version):
        dates = versions[v]
        print('\n## Version {}'.format(v))
        combined_messages = list()
        for d in sorted(dates, reverse=True):
            messages = dates[d]
            if date_group:
                last_date = d
                if len(messages) > 0:
                    print('\n### Date: {}'.format(d))
                    for message in sorted(messages):
                        print('    - {}'.format(message))
                else:
                    print('\n### Date: {}'.format(last_date))
                    print('    - Bugfixes and improvements')
            else:
                for message in messages:
                    combined_messages.append(message)
        if not date_group:
            if len(combined_messages):
                for message in sorted(combined_messages):
                    print('  - {}'.format(message))
            else:
                print('  - Bugfixes and improvements')


def write_md_commits(name, versions, date_group, output):
    try:
        f = open(output, "w")
        f.write("# {}".format(name))
        last_date = ""
        for v in sorted(versions, reverse=True, key=get_version):
            dates = versions[v]
            f.write('\n## Version {}'.format(v))
            combined_messages = list()
            for d in sorted(dates, reverse=True):
                messages = dates[d]
                if date_group:
                    last_date = d
                    if len(messages) > 0:
                        f.write('\n### Date: {}'.format(d))
                        for message in sorted(messages):
                            f.write('\n    - {}'.format(message))
                    else:
                        f.write('\n### Date: {}'.format(last_date))
                        f.write('\n    - Bugfixes and improvements')
                else:
                    for message in messages:
                        combined_messages.append(message)
            if not date_group:
                if len(combined_messages):
                    for message in sorted(combined_messages):
                        f.write('\n  - {}'.format(message))
                else:
                    f.write('\n  - Bugfixes and improvements')
        f.close()
        print('File "{}" was saved succesfully!'.format(output))
    except Exception:
        log_exception(f"An error occurred while trying to save the output file. "
                      f"Check if the specified path exists ({output}).")


def write_json_commits(name, versions, output):
    try:
        with open(output, 'w') as outfile:
            json.dump({name: {"versions": versions}}, outfile, indent=4)
        print('File "{}" was saved succesfully!'.format(output))
    except Exception:
        log_exception(f"An error occurred while trying to save the output file. "
                      f"Check if the specified path exists ({output}).")


def main():
    options = get_parsed_args()
    set_logger(options.level)
    name = get_repo_name() if options.auto_repo_name else options.name

    if not name:
        log_exception("You must specify Repo Name. "
                      "You can use --auto-name to try to auto discover it or set with --repo-name. "
                      "More help with --help")

    print(f"{__app_name} v{__app_version}: Processing '{name}' repository...")
    since = get_since(options.since)
    repo = get_repo(options.path, since)

    commits = parse_commits(repo)

    if options.format not in VALID_FORMATS:
        log_exception(f"Invalid output format. Available formats: {', '.join(VALID_FORMATS)}. More help with --help.")

    if options.format == 'md':
        if options.outfile:
            write_md_commits(name, commits, options.date_group, options.outfile)
        else:
            print_md_commits(name, commits, options.date_group)
    if options.format == 'json':
        if options.outfile:
            write_json_commits(name, commits, options.outfile)
        else:
            print(json.dumps({name: {"versions": commits}}, indent=4))


if __name__ == "__main__":
    main()
