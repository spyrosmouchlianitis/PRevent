import subprocess
import os


# TP

subprocess.run(['python', '-c', 'print("Hello World")'])

x = 'python'
subprocess.call([x, '-c', 'import sys; sys.exit()'])

subprocess.Popen(['python', '-c', 'print("Dynamic execution")'])

subprocess.check_call(['python', '-c', 'print("Check call dynamic execution")'])

subprocess.check_output(['python', '-c', 'print("Check output dynamic execution")'])

os.system('python -c "print(\'Hello World\')"')

os.popen('python -c "print(\'Popen dynamic execution\')"')

os.spawnl(os.P_WAIT, 'python', 'python', '-c', 'print("Spawn dynamic execution")')

os.spawnlp(os.P_WAIT, 'python', 'python', '-c', 'print("Spawnlp dynamic execution")')

os.execv('python', ['python', '-c', 'print("Execv dynamic execution")'])

os.execvp('python', ['python', '-c', 'print("Execvp dynamic execution")'])

X = os.system
Y = subprocess


# FP

os.system('ls')

os.popen('ls')

os.spawnl(os.P_WAIT, 'ls', 'ls')

os.execv('ls', ['ls', '-l'])

subprocess.run(['ls', '-l'])

subprocess.call(['ls', '-a'])

subprocess.Popen(['ls', '-la'])

subprocess.check_call(['ls'])

subprocess.check_output(['ls'])
