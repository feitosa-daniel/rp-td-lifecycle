import csv
import os
import tempfile
import json
import logging
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from git import Repo
from github import RateLimitExceededException, Github
import pydriller as pdl


class CachedRequests:
    def __init__(self, cache_dir=None):
        self.cache_dir = Path(cache_dir if cache_dir else tempfile.mkdtemp())
    
    def _get_remote(self, url, headers):
        return requests.get(url,headers=headers).json()
    
    def _get_cache_or_remote(self, url, headers):
        filepath = self.cache_dir.joinpath(re.sub(r'^https?://(.*)/?$',r'\1',url))
        jsonpath = filepath.joinpath('json')
        if not jsonpath.exists():
            logging.warning(url)
            filepath.mkdir(parents=True, exist_ok=True)
            with jsonpath.open('w') as f:
                res = requests.get(url,headers=headers).json()
                json.dump(res,f)
        with jsonpath.open() as f:
            return json.load(f)


class GHRequests(CachedRequests):
    def __init__(self, token=None, api_url='https://api.github.com', owner=None, repo=None, cache_dir=None):
        self.token = token
        self.api_url = api_url
        self.owner = owner
        self.repo = repo
        super().__init__(cache_dir)
    
    def _parse_details(self,owner, repo):
        u = owner if owner else self.owner
        r = repo if repo else self.repo
        return (u,r)
    
    def _get(self,endpoint, force=False):
        headers = {"accept": "application/vnd.github.v3+json",
                   "authorization": f"token {self.token}"}
        url = f'{self.api_url}{endpoint}'
        if force:
            return super()._get_remote(url,headers)
        else:
            return super()._get_cache_or_remote(url,headers)
    
    def get_pullrequests_for_commit(self,commit_sha, owner=None, repo=None):
        (o,r) = self._parse_details(owner,repo)
        endpoint = f'/repos/{o}/{r}/commits/{commit_sha}/pulls'
        return self._get(endpoint)
    
    def get_pullrequest_commits(self,pr_number, owner=None, repo=None):
        (o,r) = self._parse_details(owner,repo)
        endpoint = f'/repos/{o}/{r}/pulls/{pr_number}/commits'
        return self._get(endpoint)
    
    def get_commit_info(self,commit_sha,owner=None, repo=None):
        (o,r) = self._parse_details(owner,repo)
        endpoint = f'/repos/{o}/{r}/commits/{commit_sha}'
        return self._get(endpoint)

    def get_issue_info(self,issue_number,owner=None, repo=None):
        (o,r) = self._parse_details(owner,repo)
        endpoint = f'/repos/{o}/{r}/issues/{issue_number}'
        return self._get(endpoint)
    
    def get_api_limit_info(self):
        return self._get('/rate_limit', force=True)


class JiraRequests(CachedRequests):
    def __init__(self, api_url, cache_dir=None):
        self.api_url = api_url
        super().__init__(cache_dir)

    def _get(self,endpoint):
        headers = {"accept": "application/json"}
        url = f'{self.api_url}{endpoint}'
        return super()._get_cache_or_remote(url,headers)
    
    def get_issue_info(self, issue_key):
        endpoint = f'/issue/{issue_key}'
        return self._get(endpoint)
    
    def get_issue_reporter(self, issue_key):
        issue = self.get_issue_info(issue_key)
        reporter = issue['fields']['reporter']
        return f"{reporter['displayName']} ({reporter['name']})"
    
    def get_issue_reporting_date(self, issue_key):
        issue = self.get_issue_info(issue_key)
        date_str = issue['fields']['created']
        return date_str[:10]
    
    def get_issue_resolution_date(self, issue_key):
        issue = self.get_issue_info(issue_key)
        date_str = issue['fields']['resolutiondate']
        return date_str[:10]
    
    def get_issue_commenter(self, issue_key, comment_number):
        issue = self.get_issue_info(issue_key)
        commenter = issue['fields']['comment']['comments'][comment_number]['author']
        return f"{commenter['displayName']} ({commenter['name']})"
    
    def get_issue_commenting_date(self, issue_key, comment_number):
        issue = self.get_issue_info(issue_key)
        date_str = issue['fields']['comment']['comments'][comment_number]['created']
        return date_str[:10]
    
    def get_all_issue_commenters(self, issue_key):
        issue = self.get_issue_info(issue_key)
        return [f"{c['author']['displayName']} ({c['author']['name']})" 
                for c in issue['fields']['comment']['comments']]
    
    def get_issue_last_commenting_date(self, issue_key):
        issue = self.get_issue_info(issue_key)
        date_str = issue['fields']['comment']['comments'][-1]['created']
        return date_str[:10]


class GHRepo:
    def __init__(self, owner, repo, repos_dir=tempfile.mkdtemp(), clone_repo=True):
        self.owner = owner
        self.repo = repo
        self.local_dir = os.path.join(repos_dir, owner, repo)
        if clone_repo:
            self.clone_repo()
    
    def clone_repo(self, force=False):
        try:
            if force or not os.path.exists(self.local_dir):
                url = f'https://github.com/{self.owner}/{self.repo}'
                Repo.clone_from(url, self.local_dir)
                logging.debug(f'Cloned {self.owner}/{self.repo} to {self.local_dir}')
            logging.debug(f'{self.local_dir} already exists')
        except:
            logging.error(f'Could not clone {self.owner}/{self.repo}')
    
    # More traverse options:
    #   https://pydriller.readthedocs.io/en/latest/repository.html#filtering-commits
    def traverse_all_commits(self):
        return pdl.Repository(self.local_dir).traverse_commits()

    def get_commit(self, commit_sha):
        return next(pdl.Repository(self.local_dir, single=commit_sha).traverse_commits())
    
    def get_commit_author(self, commit_sha):
        try:
            c = self.get_commit(commit_sha)
            return f"{c.author.name} ({c.author.email})"
        except:
            logging.error(f'Commit not found: {self.owner}/{self.repo} {commit_sha}')
            return '-'
    
    def get_commit_date(self, commit_sha):
        try:
            c = self.get_commit(commit_sha)
            return c.author_date.strftime("%Y-%m-%d")
        except:
            logging.error(f'Commit not found: {self.owner}/{self.repo} {commit_sha}')
            return '-'

    
def find_commits_jira_issues(gh_repo):
    issue_commits = {}
    for commit in gh_repo.traverse_all_commits():
        #Jira issue pattern PROJECT-<issue_number>, we used a regex to filter the commits
        closed_issues = re.findall(r'(\w+-\d+)', commit.msg.upper(), re.DOTALL)
        for ci in closed_issues:
            issue_commits[ci] = issue_commits.get(ci, []) + [commit.hash]
    return issue_commits


def days_between(d1, d2):
    if re.search(r'^\d\d\d\d-\d\d-\d\d$', d1) and re.search(r'^\d\d\d\d-\d\d-\d\d$', d2):
        d1 = datetime.strptime(d1, "%Y-%m-%d")
        d2 = datetime.strptime(d2, "%Y-%m-%d")
        return abs((d2 - d1).days)
    else:
        return 'unknown'


def in_list(cotainee, container):
    if isinstance(cotainee,str):
        return cotainee in container
    else:
        return any([c in container for c in cotainee])
    

def in_list_count(cotainee, container):
    if isinstance(cotainee,str):
        return cotainee in container
    else:
        return any([c in container for c in cotainee])


def load_csv_dataset(filename, dialect='excel'):
    with open(filename, 'r') as f:
        reader = csv.DictReader(f, dialect=dialect)
        return [row for row in reader]

    
def save_csv_dataset(filename, data, header=None):
    header = header if header else list(data[0].keys())
    with open(filename, 'w') as f:
        writer = csv.DictWriter(f,fieldnames=header)
        writer.writeheader()
        for d in data:
            writer.writerow(d)

def dict_csv_to_dataframe(dataset):
    return pd.DataFrame.from_records(dataset)


