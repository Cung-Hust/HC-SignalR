import subprocess

def execute(cmd: str):
    s = subprocess.getstatusoutput(cmd)

def execute_with_result(cmd: str) -> tuple:
    s = subprocess.getstatusoutput(cmd)
    return s

