#!/usr/bin/python

import requests
import argparse
import subprocess
import time
import json
import signal
import sys
import os

AdminToken=''
BackupFolderPath='./backup'
CookieFilePath='cookies.txt'
SavedFilesDB='.slut-bak.json'
TeamInfoDb='.team-bak.json'
LsDb='.ls-bak.json'
UserDb='.user-bak.json'
TeamName=''

should_exit=False

def signal_handler(signal, frame):
    global should_exit
    should_exit = True
    print 'slut.py asked to exit, cleaning up'

def ls_db_path():
    return '.'+TeamName+'/'+LsDb

def team_info_db_path():
    return '.'+TeamName+'/'+TeamInfoDb

def saved_files_db_path():
    return '.'+TeamName+'/'+SavedFilesDB

def backup_team_folder_path():
    return BackupFolderPath+'/'+TeamName

def user_db_path():
    return '.'+TeamName+'/'+UserDb

def ensure_team_folder_exists():
    # if not exist create it
    if not os.path.exists('.'+TeamName):
        os.makedirs('.'+TeamName)

def make_request(request_str):
    # try to get the data from the current page
    r = requests.get(request_str)
    if r.status_code != 200:
        print 'cannot request slack information, check your token'
        sys.exit(0)

    # convert response into json dict
    json = r.json()

    # if not ok -> not enough access
    if json['ok'] != True:
        print 'valid request but not enough rights, check your token'
        sys.exit(0)

    return json

def get_files_for_page(current_page, max_pages):
    print 'fetching files from page: {}/{}'.format(current_page, max_pages)

    # generete the url for the request
    request_str = 'https://slack.com/api/files.list?token={}&page={}'.format(AdminToken,current_page)
    json = make_request(request_str)

    # our files list
    lst = []

    # iterate over each files for the curent page
    for f in json['files']:
        lst.append(f)

    return lst

def get_all_files_list(pages_count, should_update):
    # if data already exist
    if not should_update:
        if os.path.exists(ls_db_path()):
            with open(ls_db_path(), 'rb') as f:
                j = json.loads(f.read())
                return j

    # else retrieve data
    print 'retrieving list of all available files ({} pages)'.format(pages_count)
    files = []
    for p in range(1, pages_count+1):
        if should_exit:
            return []
        files = files + get_files_for_page(p, pages_count)

    # save in file
    with open(ls_db_path(), 'wb') as outfile:
        json.dump(files, outfile, indent=2)

    return files

def get_team_name():
    global TeamName
    print 'retrieving team information:',

    # if data already exist
    if os.path.exists(team_info_db_path()):
        with open(team_info_db_path(), 'rb') as f:
            j = json.loads(f.read())
            print '{}'.format(j['team']['name'])
            return

    # else
    request_str = 'https://slack.com/api/team.info?token={}'.format(AdminToken)
    json_value = make_request(request_str)

    if json_value['ok'] != True:
        print '\nvalid request but not enough rights, check your token'
        sys.exit(0)

    TeamName = json_value['team']['domain']
    print '{}'.format(json_value['team']['name'])

    ensure_team_folder_exists()

    # save team info
    with open(team_info_db_path(), 'wb') as outfile:
        json.dump(json_value, outfile, indent=2)

def get_user_list():
    # if data already exist
    if os.path.exists(user_db_path()):
        with open(user_db_path(), 'rb') as f:
            j = json.loads(f.read())
            return j

    # else
    request_str = 'https://slack.com/api/users.list?token={}'.format(AdminToken)
    json_value = make_request(request_str)

    if json_value['ok'] != True:
        print 'valid request but not enough rights, check your token'
        sys.exit(0)

    ensure_team_folder_exists()

    # save user info
    with open(user_db_path(), 'wb') as outfile:
        json.dump(json_value, outfile, indent=2)

    return json_value

def get_pages_count():
    # generete the url for the request
    request_str = 'https://slack.com/api/files.list?token={}'.format(AdminToken)
    json = make_request(request_str)

    # if not ok -> not enough access
    if json['ok'] != True:
        print 'valid request but not enough rights, check your token'
        sys.exit(0)

    return int(json['paging']['pages'])

def parse_args():
    # general parser
    parser = argparse.ArgumentParser(description='Slack utilities')
    subparsers = parser.add_subparsers(help='available commands')

    # create the parser for the backup command
    parser_backup = subparsers.add_parser('backup', help='backup all files from slack')
    parser_backup.add_argument('backup_value', nargs='?', help='backup files from slack')
    parser_backup.add_argument('--token', nargs='+', help='the token to use to launch requests')
    parser_backup.add_argument('--cookies', nargs='+', help='path to the cookies to retrieve files')
    parser_backup.add_argument('--output', nargs='+', help='path to save the files')
    parser_backup.add_argument('--update', action='store_true', help='force update of the local db')

    # create the parser for the rm command
    parser_rm = subparsers.add_parser('rm', help='remove files from slack')
    parser_rm.add_argument('rm_value', nargs='?', default='30', help='remove files from slack')
    parser_rm.add_argument('--token', nargs='+', help='the token to use to launch requests')

    parser_ls = subparsers.add_parser('ls', help='list files uploaded on slack')
    parser_ls.add_argument('ls_value', nargs='?', default='30', help='list files uploaded slack')
    parser_ls.add_argument('--update', action='store_true', help='force update of the local db')
    parser_ls.add_argument('--token', nargs='+', help='the token to use to launch requests')

    return parser.parse_args()

def get_saved_files():
    if os.path.exists(saved_files_db_path()):
        with open(saved_files_db_path(), 'rb') as f:
            return json.loads(f.read())
    return []

def save_files(files):
    with open(saved_files_db_path(), 'wb') as outfile:
        json.dump(files, outfile, indent=2)

def file_exist(files_list, f):
    for e in files_list:
        if e['name'] == f['name'] and e['saved_name'] == f['saved_name'] and e['id'] == f['id'] and e['path'] == f['path']:
            return True
    return False

def do_backup(files):
    # build user specified folder if not exist
    if not os.path.exists(BackupFolderPath):
        os.makedirs(BackupFolderPath)
    # build team folder if not exist
    if not os.path.exists(backup_team_folder_path()):
        os.makedirs(backup_team_folder_path())

    # get list of already saved files
    saved_files = get_saved_files()
    file_cnt = len(files)
    file_it = 1

    # get all files
    for f in files:
        # check if user asked for exit
        if should_exit == True:
            break;

        # get required datas
        cur_f = {}
        cur_f['name'] = f['name']
        cur_f['saved_name'] = u'{}-{}'.format(f['timestamp'], f['name'])
        cur_f['id'] = f['id']
        cur_f['path'] = '{}/{}-{}'.format(backup_team_folder_path(), f['timestamp'], f['name'])
        # file do not exist get + add it to the db
        sys.stdout.write(u'{}/{} '.format(file_it, file_cnt))
        sys.stdout.flush()
        if not file_exist(saved_files, cur_f):
            subprocess.call([
                u'wget',
                u'--no-verbose',
                u'--load-cookies={}'.format(CookieFilePath),
                u'--output-document={}/{}-{}'.format(backup_team_folder_path(), f['timestamp'], f['name']),
                f['url_private']])
            saved_files.append(cur_f)
        # file exist do nothin
        else:
            print u'{}/{}-{} already exist.'.format(backup_team_folder_path(), f['timestamp'], f['name'])
        file_it+=1
    save_files(saved_files)

def user_name_from_id(user_id, users):
    for user in users:
        if user_id == user['id']:
            return user['name']
    return ""

def do_ls(files):
    users = get_user_list()["members"]

    for f in files:
        uname = user_name_from_id(f['user'], users)
        print u'{} {} {} {}'.format(f['id'], uname, time.ctime(f['timestamp']), f['name']).encode('unicode-escape')

def do_remove(files, days):
    print files

def main():
    global AdminToken
    global CookieFilePath
    global BackupFolderPath
    # catch signals
    signal.signal(signal.SIGINT, signal_handler)
    # get / validate arguments
    raw_args = parse_args()
    args = vars(raw_args)

    # check if token is specified
    if raw_args.token == None:
        print 'error you need to specify a slack token'
        sys.exit(0)
    else:
        AdminToken = raw_args.token[0]

    # retrieve team nam
    get_team_name()

    # get user list
    get_user_list()

    # get pages count
    pages_count = get_pages_count()

    # iterate over all pages
    files = get_all_files_list(pages_count, raw_args.update)

    # backup
    if 'backup_value' in args.keys():
        # if cookie option specified
        if raw_args.cookies == None:
            print 'no cookies file specified, using default'
        else:
            CookieFilePath = raw_args.cookies[0]
        # if out-folder specified
        if raw_args.output == None:
            print 'no ouput folder speicified using default'
        else:
            BackupFolderPath = raw_args.output[0]
        do_backup(files)
    elif 'ls_value' in args.keys():
        do_ls(files)
    elif 'rm_value' in args.keys():
        do_remove(files, args['rm_value'])

if __name__ == "__main__":
    main()
