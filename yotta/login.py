# Github Access, , access repositories on github, internal
from lib import github_access

def addOptions(parser):
    parser.add_argument('username', default=None,
        help='Your GitHub username. Yotta securely federates login to GitHub, your password is not stored.'
    )

def execCommand(args):
    github_access.authorizeUser(args.username)

