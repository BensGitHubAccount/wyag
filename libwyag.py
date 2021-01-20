import argparse
import collections
import configparser
import hashlib
import os
import re
import sys
import zlib
# from https://wyag.thb.lt/

argparser = argparse.ArgumentParser(description="content tracker")
argsubparsers = argparser.add_subparsers(title='commands', dest='command')
argsubparsers.required = True

def main(argv=sys.argv[1:]):
    args = argparser.parse_args(argv)

    if   args.command == "add"         : cmd_add(args)
    elif args.command == "cat-file"    : cmd_cat_file(args)
    elif args.command == "checkout"    : cmd_checkout(args)
    elif args.command == "commit"      : cmd_commit(args)
    elif args.command == "hash-object" : cmd_hash_object(args)
    elif args.command == "init"        : cmd_init(args)
    elif args.command == "log"         : cmd_log(args)
    elif args.command == "ls-tree"     : cmd_ls_tree(args)
    elif args.command == "merge"       : cmd_merge(args)
    elif args.command == "rebase"      : cmd_rebase(args)
    elif args.command == "rev-parse"   : cmd_rev_parse(args)
    elif args.command == "rm"          : cmd_rm(args)
    elif args.command == "show-ref"    : cmd_show_ref(args)
    elif args.command == "tag"         : cmd_tag(args)

class GitException(Exception):
    pass

def repo_path(repo, *path):
    """Compute path under repo's gitdir."""
    return os.path.join(repo.gitdir, *path)
        
def repo_file(repo, *path, mkdir=False):
    """
    Same as repo_path but will create dirname(*path) if absent.
    Ex: repo_file(f, "refs", "remotes", "origin", "HEAD") will create .git/refs/remotes/origin
    """
    if repo_dir(repo, *path[:-1], mkdir=mkdir):
        return repo_path(repo, *path)
    
def repo_dir(repo, *path, mkdir=False):
    """Same as repo_path, but mkdir *path if absent """
    path = repo_path(repo, *path)

    if os.path.exists(path):
        if (os.path.isdir(path)):
            return path
        else:
            raise GitException(f"Not a directory {path}")

    if mkdir:
        os.makedirs(path)
        return path
    else:
        return None

class GitRepo(object):
    """A git repository"""

    worktree = None
    gitdir = None
    conf = None

    def __init__(self, path, force=False):
        self.worktree = path
        self.gitdir = os.path.join(path, ".git")

        if not (force or os.path.isdir(self.gitdir)):
            raise GitException(f"Not a Git repository {path}")

        # Read config file in .git/config
        self.conf = configparser.ConfigParser()
        cf = repo_file(self, "config")

        if cf or os.path.exists(cf):
            self.conf.read([cf])
        elif not force:
            raise GitException("Config file missing")

        if not force:
            vers = int(self.conf.get("core", "repositoryformatversion"))
            if vers != 0:
                raise GitException(f"Unsuppoerted repositoryformatversion {vers}")


def repo_create(path):
    """Create a new repo at path"""
    repo = GitRepo(path, force=True)

    # First make sure the path either doesn't exist or is empty.
    if os.path.exists(repo.worktree):
        if not os.path.isdir(repo.worktree):
            raise GitException(f"{path} is not a directory")
        if os.listdir(repo.worktree):
            raise GitException(f"{path} is not empty")
    else:
        os.makedirs(repo.worktree)

    assert(repo_dir(repo, "branches", mkdir=True))
    assert(repo_dir(repo, "objects", mkdir=True))
    assert(repo_dir(repo, "refs", "tags", mkdir=True))
    assert(repo_dir(repo, "refs", "heads", mkdir=True))

    # .git/description
    with open(repo_file(repo, "description"), "w") as f:
        f.write("Unnamed repository; edit this file 'description' to name repository.\n")

    # .git/HEAD
    with open(repo_file("HEAD"), "w") as f:
        f.write("ref: refs/heads/master\n")

    with open(repo_file(repo, "config"), "w") as f:
        config = repo_default_config()
        config.write(f)
    # TODO: Is the above line correct? 
    return repo

def repo_default_config():
    ret = configparser.ConfigParser()
    ret.add_section("core")
    ret.set("core", "repositoryformatversion", "0")
    ret.set("core", "filemode", "false")
    ret.set("core", "bare", "false")
    return ret

argsp = argsubparsers.add_parser("init", help="Initialize a new, empty repository.")
argsp.add_argument("path",
                   metavar="directory",
                   nargs="?",
                   default=".",
                   help="Where to create the repo")

def cmd_init(args):
    repo_create(args.path)

def repo_find(path=".", required=True):
    path = os.path.realpath(path)

    if os.path.isdir(os.path.join(path, '.git')):
        return GitRepo(path)
    
    # If haven't returned, recurse in parent
    parent = os.path.realpath(os.path.join(path, '..'))

    if parent == path:
        # bottom case
        # os.path.join("/", "..") = "/":
        # If parent==path, then path is root.
        if required:
            raise GitException("No git directory")
        else:
            return None

    # recurse
    return repo_find(parent, required=required)

# stopped at 4.1















