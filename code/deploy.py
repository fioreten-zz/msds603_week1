import paramiko
from os.path import expanduser
from user_definition import *


# ## Assumption : Anaconda, Git (configured)

def ssh_client():
    """Return ssh client object"""
    return paramiko.SSHClient()


def ssh_connection(ssh, ec2_address, user, key_file):
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ec2_address, username=user,
                key_filename=expanduser("~") + key_file)
    return ssh


def create_or_update_environment(ssh):
    stdin, stdout, stderr = \
        ssh.exec_command("conda env create -f "
                         "~/" + git_repo_name + "/environment.yml")
    if (b'already exists' in stderr.read()):
        stdin, stdout, stderr = \
            ssh.exec_command("conda env update -f "
                             "~/" + git_repo_name + "/environment.yml")

    # now, we activate the environment
    stdin, stdout, stderr = ssh.exec_command("source activate MSDS603")
    print(stdout.read())
    print(stderr.read())


def git_clone(ssh):

    # install git
    stdin, stdout, stderr = ssh.exec_command("sudo yum -y install git")
    stdin, stdout, stderr = ssh.exec_command("git config --global credential.helper store")

    # now we proceed to clone the repository
    stdin, stdout, stderr = ssh.exec_command("git --version")
    if (b"" is stderr.read()):
        # we must also assume that the user access has already been granted
        git_clone_command = "git clone https://github.com/" + \
                            git_user_id + "/" + git_repo_name + ".git"
        stdin, stdout, stderr = ssh.exec_command(git_clone_command)
        print(stdout.read())
        print(stderr.read())

        # if the git repo name already exists
        if (b"" is not stderr.read()):
            git_pull_command = "cd " + git_repo_name + "; git pull"
            stdin, stdout, stderr = ssh.exec_command(git_pull_command)
        

def set_up_contrab(ssh):
    # at this point, we alread have the repo cloned (or updated)
    # now, we need to set up the contab
    full_path_repo = f"/home/{user}/{git_repo_name}/code/calculate_driving_time.py"
    full_path_env = f"~/.conda/envs/MSDS603/bin/python"
    contrab_code = f"* * * * * {full_path_env} {full_path_repo}"
    final_code = f"crontab -e; {contrab_code}"
    stdin, stdout, stderr = ssh.exec_command(
        f'crontab <(cat <(crontab -l 2>/dev/null) <(echo "{contrab_code}"))')

    print(stdout.read())
    print(stderr.read())



def main():
    ssh = ssh_client()
    ssh_connection(ssh, ec2_address, user, key_file)
    git_clone(ssh)
    create_or_update_environment(ssh)
    set_up_contrab(ssh)


if __name__ == '__main__':
    main()
