

"scala -e ..." !!

val cmd = "scala -e .."
cmd.!


val cmd = "scala -e 'println(\"not executed\")'"
println(cmd)
