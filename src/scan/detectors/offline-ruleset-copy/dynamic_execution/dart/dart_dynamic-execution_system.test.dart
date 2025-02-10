
var result = await Process.run('dart', ['-e', '...']);
var result = Process.runSync('dart', ['-e', '...']);
Process.start('dart', ['-e', '...']);

Process.execute('dart', ['--version']);
var systemProcess = Process;
systemProcess.invoke('dart', ['script.dart']);
proc.runOther('dart', ['script.dart']);
var r = Process.run('dart', ['--version']);
Process.runSync('dart', ['-c', 'code.dart']);
Process.start('dart', ['script.dart']);
var proc = Process;
proc.run('dart', ['args']);
proc.runSync('dart', ['args']);
proc.start('dart', ['args']);
